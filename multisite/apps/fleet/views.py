"""Les pages de la flotte, et le seul bouton qui peut agir sur une machine."""

from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.core.mixins import ConsolePageMixin, StaffRequiredMixin, ViewerRequiredMixin
from www.render_utils import fleet_subpages

from . import ntfy
from .models import Machine, Stack
from .state import build_state


class FleetBaseView(ViewerRequiredMixin, ConsolePageMixin, TemplateView):
    """Socle des deux pages de la flotte : l'état complet et la sous-navigation.

    Les machines et les stacks se lisent dans le même état assemblé, mais tiennent
    chacune une page : deux grands tableaux à la suite ne se comparaient pas.
    """

    nav_page = "fleet:index"
    subpages = fleet_subpages

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(build_state())
        # Les deux états qu'aucun autre contrôle du lab ne voit : gatus voit des
        # conteneurs sains et wud une image à jour, donc ce sont ces pages ou rien.
        # `present` seulement : une stack déplacée ou supprimée n'a plus de conteneurs,
        # donc plus de compose à réparer — l'alerte qu'elle portait était indéfinie et
        # sans remède, c'est-à-dire du bruit.
        ctx["stack_alerts"] = [
            stack
            for row in ctx["machines"]
            for stack in row["stacks"]
            if stack.present
            and stack.compose in (Stack.Compose.MISSING, Stack.Compose.UNTRACKED)
        ]
        # Reste-t-il quelque chose à attendre ? C'est au serveur de le dire, parce que
        # lui seul sait si un rapport est arrivé depuis la demande. La page se
        # rechargeait auparavant un nombre fixe de fois, et une action longue --
        # quatorze minutes de `pacman -Syu` sur hecate -- se terminait bien après que la
        # page avait renoncé.
        ctx["attente_active"] = any(
            row["action_en_cours"] or any(s.deploiement_en_cours for s in row["stacks"])
            for row in ctx["machines"]
        )
        return ctx


class FleetView(FleetBaseView):
    """Les machines déclarées : état rapporté, mises à jour, disque, dérive, images."""

    template_name = "fleet/index.html"
    page_title = "Flotte"
    subpage_title = "Machines"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["verbs"] = ntfy.VERB_LABELS
        return ctx


class StacksView(FleetBaseView):
    """Les stacks compose déployées, machine par machine."""

    template_name = "fleet/stacks.html"
    page_title = "Stacks déployées"
    subpage_title = "Stacks"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Ne garder que les machines qui rapportent au moins une stack, pour que la
        # page puisse dire « aucune » sans lister des machines vides.
        ctx["machines"] = [row for row in ctx["machines"] if row["stacks"]]
        toutes = [stack for row in ctx["machines"] for stack in row["stacks"]]
        # Les compteurs ne portent que sur ce qui est déployé : compter le retard git
        # d'une stack qui n'existe plus, c'est annoncer un travail à faire qui n'en est
        # pas un. Les disparues ont leur propre compteur, et leur bouton pour partir.
        vivantes = [s for s in toutes if s.present]
        # Les deux retards sont comptés séparément : un compose jamais appliqué et une
        # image dont le tag a bougé ne se soignent pas de la même façon.
        ctx["stacks_total"] = len(vivantes)
        ctx["stacks_git_en_retard"] = sum(1 for s in vivantes if s.git_en_retard)
        ctx["stacks_images_en_retard"] = sum(1 for s in vivantes if s.images["behind"])
        ctx["stacks_deployables"] = sum(1 for s in vivantes if s.deployable)
        ctx["stacks_absentes"] = len(toutes) - len(vivantes)
        return ctx


def _voir_autre_page(url_name, *args):
    """Redirige en 303, pour qu'un rafraîchissement ne rejoue pas le POST.

    Aucun marqueur dans l'URL : la page se recharge d'elle-même tant que le serveur
    déclare `attente_active`, ce qu'il lit dans `action_requested_at` et
    `deploy_requested_at`. Un paramètre ne pouvait porter qu'un compteur aveugle, et un
    compteur aveugle a déjà renoncé quinze minutes trop tôt sur un `upgrade` de hecate.
    """
    response = redirect(url_name, *args)
    response.status_code = 303
    return response


def _rapport_de_suivi(verb, machine):
    """Fait suivre une action d'une demande de rapport, et dit ce que ça change.

    L'agent de la machine traite les messages du sujet **en série** : ce rapport ne
    partira donc qu'une fois l'action terminée, et il n'y a rien à ordonnancer ici.

    C'est ce qui manquait, et c'était tout le sujet de « le bouton ne fait pas ce qu'on
    espère » : l'action partait bien et le script s'exécutait, mais la page continuait
    d'afficher le dernier rapport horaire — jusqu'à cinquante minutes en arrière selon la
    machine. Le `behind` ne bougeait pas, le `Vu` ne bougeait pas, donc rien ne prouvait
    qu'il s'était passé quelque chose.

    Pas de rapport de suivi après `report` : c'en est déjà un.
    """
    if verb == "report":
        return ""
    if ntfy.publish("report", machine):
        return " (le rapport de suivi n'a pas pu être publié)"
    return " — un rapport suivra dès que ce sera terminé, cette page se rafraîchit seule"


# Les deux seules pages sur lesquelles une action peut renvoyer. Une liste blanche et
# non le `Referer` ou un `next` libre : un paramètre de redirection non contraint est
# une redirection ouverte, et il n'y a ici que deux destinations à connaître.
PAGES_DE_RETOUR = ("fleet:index", "fleet:stacks")


def _page_de_retour(request, defaut):
    """La page où revenir après une action, prise dans la liste blanche."""
    demandee = request.POST.get("retour")
    return demandee if demandee in PAGES_DE_RETOUR else defaut


class ApproveView(StaffRequiredMixin, View):
    """Publie une approbation pour une machine.

    Atteindre cet endpoint ne permet pas d'exécuter une commande : il écrit un
    message nommant l'un des quatre verbes sur un sujet ntfy. Voir `apps/fleet/ntfy.py`.

    Le champ `retour` sert au bouton « Demander un rapport » de la page Stacks : sans
    lui, rafraîchir une ligne renvoyait sur la page Machines, ce qui fait perdre
    l'endroit qu'on regardait.
    """

    def post(self, request, machine, verb):
        error = ntfy.publish(verb, machine)
        if error:
            messages.error(request, error)
        else:
            # Après la publication, jamais avant : une demande qui n'est pas partie ne
            # doit pas s'afficher « en cours ».
            Machine.objects.filter(name=machine).update(
                action_requested_at=timezone.now(), action_requested_verb=verb
            )
            suite = _rapport_de_suivi(verb, machine)
            messages.success(request, f"« {verb} » publié pour {machine}{suite}")
        return _voir_autre_page(_page_de_retour(request, "fleet:index"))


class DeployStackView(StaffRequiredMixin, View):
    """Demande la mise à jour d'une stack par son script de déploiement.

    Même contrat que `ApproveView` : la console publie un verbe et deux noms validés
    en base, et c'est l'agent de la machine qui retrouve et lance le script.
    """

    def post(self, request, machine, project):
        error = ntfy.publish_deploy(machine, project)
        if error:
            messages.error(request, error)
        else:
            # Horodaté après la publication, jamais avant : marquer « en cours » une
            # demande qui n'est pas partie ferait mentir la page dans le seul cas où
            # elle doit être crue.
            Stack.objects.filter(
                machine__name=machine, project=project, present=True,
            ).update(deploy_requested_at=timezone.now())
            suite = _rapport_de_suivi("deploy", machine)
            messages.success(
                request, f"Mise à jour demandée pour {machine}/{project}{suite}"
            )
        return _voir_autre_page("fleet:stacks")


class ForgetStackView(StaffRequiredMixin, View):
    """Retire de la base la ligne d'une stack qui n'est plus déployée.

    La seule suppression de toute la flotte, et elle ne touche que cette console : la
    machine n'en sait rien. Elle existe parce qu'une stack déplacée ou supprimée
    laissait une ligne que rien ne pouvait plus mettre à jour — la sonde ne la rapporte
    plus, donc son état restait figé au dernier instant où elle a été vue à moitié
    démontée.

    Une stack encore rapportée est refusée : la supprimer ne ferait rien, le prochain
    rapport la recréerait en perdant son `first_seen`.
    """

    def post(self, request, pk):
        """Supprime la ligne, si et seulement si elle n'est plus rapportée."""
        stack = Stack.objects.filter(pk=pk).select_related("machine").first()
        if stack is None:
            messages.error(request, "Cette stack n'existe plus.")
        elif stack.present:
            messages.error(
                request,
                f"{stack} est encore rapportée par sa machine : rien à oublier.",
            )
        else:
            nom = str(stack)
            stack.delete()
            messages.success(request, f"{nom} a été oubliée.")
        return _voir_autre_page("fleet:stacks")


class ForgetGoneStacksView(StaffRequiredMixin, View):
    """Oublie d'un coup toutes les stacks que plus aucune machine ne rapporte.

    Un bouton par ligne suffisait mal : le cas courant est un ménage dans le lab, qui
    en laisse plusieurs derrière lui d'un coup.
    """

    def post(self, request):
        """Supprime toutes les lignes marquées absentes du dernier rapport."""
        disparues = Stack.objects.filter(present=False)
        nombre = disparues.count()
        disparues.delete()
        if nombre:
            pluriel = "s" if nombre > 1 else ""
            messages.success(request, f"{nombre} stack{pluriel} oubliée{pluriel}.")
        else:
            messages.info(request, "Aucune stack disparue à oublier.")
        return _voir_autre_page("fleet:stacks")
