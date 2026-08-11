"""Les pages de la flotte, et le seul bouton qui peut agir sur une machine."""

from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from apps.core.mixins import ConsolePageMixin, StaffRequiredMixin, ViewerRequiredMixin
from www.render_utils import fleet_subpages

from . import ntfy
from .models import Stack
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
        ctx["stack_alerts"] = [
            stack
            for row in ctx["machines"]
            for stack in row["stacks"]
            if stack.compose in (Stack.Compose.MISSING, Stack.Compose.UNTRACKED)
        ]
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
        # Les deux retards sont comptés séparément : un compose jamais appliqué et une
        # image dont le tag a bougé ne se soignent pas de la même façon.
        ctx["stacks_total"] = len(toutes)
        ctx["stacks_git_en_retard"] = sum(1 for s in toutes if s.git_en_retard)
        ctx["stacks_images_en_retard"] = sum(1 for s in toutes if s.images["behind"])
        ctx["stacks_deployables"] = sum(1 for s in toutes if s.deployable)
        return ctx


def _voir_autre_page(url_name, *args):
    """Redirige en 303, pour qu'un rafraîchissement ne rejoue pas le POST."""
    response = redirect(url_name, *args)
    response.status_code = 303
    return response


class ApproveView(StaffRequiredMixin, View):
    """Publie une approbation pour une machine.

    Atteindre cet endpoint ne permet pas d'exécuter une commande : il écrit un
    message nommant l'un des quatre verbes sur un sujet ntfy. Voir `apps/fleet/ntfy.py`.
    """

    def post(self, request, machine, verb):
        error = ntfy.publish(verb, machine)
        if error:
            messages.error(request, error)
        else:
            messages.success(request, f"« {verb} » publié pour {machine}")
        return _voir_autre_page("fleet:index")


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
            messages.success(request, f"Mise à jour demandée pour {machine}/{project}")
        return _voir_autre_page("fleet:stacks")
