"""Tests de la flotte : ingestion des rapports, retards, et demande de déploiement."""
from unittest import mock

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from common.user_utils import ADMINISTRATEUR

from . import ntfy, wud
from .ingest import store
from .models import Machine, Stack
from .state import _attacher_images

RAPPORT = {
    "schema": 1,
    "at": "2026-08-11T10:00:00Z",
    "facts": {"os": "Debian 12", "uptime": "3 jours"},
    "stacks": [
        {
            "project": "immich",
            "path": "/srv/stacks/immich",
            "compose": "tracked",
            "behind": "2",
            "deploy": "deploy.sh",
        },
    ],
}


def _machine(nom="selene", ip="10.10.0.10"):
    """Une machine déclarée de l'inventaire."""
    return Machine.objects.create(name=nom, ip=ip)


def _admin():
    """Un utilisateur staff : `is_staff` est dérivé du niveau par UserProfile.save()."""
    user = User.objects.create_user(username="admin", password="motdepasse")
    user.userprofile.user_level = ADMINISTRATEUR
    user.userprofile.save()
    user.refresh_from_db()
    return user


class IngestDeployScriptTest(TestCase):
    """Le champ `deploy` du rapport, et la tolérance quand il manque."""

    def setUp(self):
        self.machine = _machine()

    def test_script_rapporte_est_enregistre(self):
        """Un nom de script est repris tel quel."""
        store(self.machine, RAPPORT)
        stack = Stack.objects.get(project="immich")
        self.assertEqual(stack.deploy_script, "deploy.sh")
        self.assertTrue(stack.deployable)

    def test_champ_absent_reste_vide(self):
        """Une sonde qui ne connaît pas le champ ne rend pas la stack déployable."""
        payload = {**RAPPORT, "stacks": [{"project": "gatus", "path": "/srv/stacks/gatus"}]}
        store(self.machine, payload)
        stack = Stack.objects.get(project="gatus")
        self.assertEqual(stack.deploy_script, "")
        self.assertFalse(stack.deployable)

    def test_tiret_signifie_pas_de_script(self):
        """`-` est la façon qu'a la sonde d'écrire « rien »."""
        payload = {**RAPPORT, "stacks": [{**RAPPORT["stacks"][0], "deploy": "-"}]}
        store(self.machine, payload)
        self.assertEqual(Stack.objects.get(project="immich").deploy_script, "")

    def test_chemin_refuse(self):
        """Seul un nom de fichier est accepté : un chemin vient de la machine."""
        for valeur in ("../../etc/passwd", "/usr/bin/env", "./deploy.sh", 42):
            with self.subTest(valeur=valeur):
                payload = {**RAPPORT, "stacks": [{**RAPPORT["stacks"][0], "deploy": valeur}]}
                store(self.machine, payload)
                self.assertEqual(Stack.objects.get(project="immich").deploy_script, "")

    def test_compose_disparu_bloque_le_deploiement(self):
        """Un script sans compose exploitable ne peut pas aboutir."""
        payload = {**RAPPORT, "stacks": [{**RAPPORT["stacks"][0], "compose": "missing"}]}
        store(self.machine, payload)
        stack = Stack.objects.get(project="immich")
        self.assertEqual(stack.deploy_script, "deploy.sh")
        self.assertFalse(stack.deployable)


class LibelleComposeTest(TestCase):
    """La colonne « Compose » de la page Stacks, restée vide depuis le premier jour.

    `get_compose_display()` n'existe que si le champ déclare ses `choices` ; sans eux le
    gabarit avale l'attribut manquant en silence, sans erreur et sans texte. Le test
    porte sur l'affichage rendu, pas seulement sur la méthode : c'est la cellule vide
    qui était le symptôme.
    """

    def setUp(self):
        self.machine = _machine()
        _admin()
        self.client.login(username="admin", password="motdepasse")

    def test_chaque_etat_a_un_libelle(self):
        """Les cinq états rapportables par la sonde ont un texte lisible."""
        attendus = {
            "tracked": "Suivi par git",
            "untracked": "Jamais commité",
            "missing": "Fichier disparu",
            "no-git": "Hors dépôt git",
            "-": "Inconnu",
        }
        for valeur, libelle in attendus.items():
            with self.subTest(compose=valeur):
                stack = Stack(machine=self.machine, project="p", path="/a", compose=valeur)
                self.assertEqual(stack.get_compose_display(), libelle)

    def test_la_colonne_est_rendue(self):
        """La cellule porte le libellé, et non le vide qu'on y lisait."""
        store(self.machine, RAPPORT)
        with mock.patch("apps.fleet.state.wud.containers", return_value=([], None)):
            response = self.client.get(reverse("fleet:stacks"))
        self.assertContains(response, "Suivi par git")


class StackDisparueTest(TestCase):
    """Une stack déplacée ou supprimée : plus rapportée, donc plus alarmante.

    C'est le cas qui rendait une alerte impossible à faire taire. La sonde dérive la
    liste des stacks des conteneurs que Docker déclare : dès que la stack part, sa ligne
    n'est plus mise à jour et reste figée sur le dernier état vu — souvent
    `compose: missing`, puisque c'est l'instant du déménagement. La page annonçait alors
    pour toujours une stack sans compose exploitable, et rien ne pouvait la corriger.
    """

    def setUp(self):
        self.machine = _machine()
        store(self.machine, RAPPORT)

    def _rapport(self, at, stacks):
        """Un rapport suivant, avec la liste de stacks donnée."""
        return {**RAPPORT, "at": at, "stacks": stacks}

    def test_stack_absente_du_rapport_perd_present(self):
        """La liste rapportée est complète : ce qui n'y est plus n'est plus déployé."""
        store(self.machine, self._rapport("2026-08-11T11:00:00Z", []))
        self.assertFalse(Stack.objects.get(project="immich").present)

    def test_stack_deplacee_laisse_l_ancienne_ligne(self):
        """Un déplacement crée la nouvelle ligne et rend l'ancienne au passé."""
        deplacee = {**RAPPORT["stacks"][0], "path": "/srv/docker/immich"}
        store(self.machine, self._rapport("2026-08-11T11:00:00Z", [deplacee]))
        etats = {s.path: s.present for s in Stack.objects.filter(project="immich")}
        self.assertEqual(etats, {"/srv/stacks/immich": False, "/srv/docker/immich": True})

    def test_une_absente_ne_porte_plus_de_gravite(self):
        """Le `compose: missing` d'une stack partie ne se répare pas : plus d'alerte."""
        casse = {**RAPPORT["stacks"][0], "compose": "missing"}
        store(self.machine, self._rapport("2026-08-11T11:00:00Z", [casse]))
        stack = Stack.objects.get(project="immich")
        self.assertEqual(stack.severity, "danger")

        store(self.machine, self._rapport("2026-08-11T12:00:00Z", []))
        stack.refresh_from_db()
        self.assertEqual(stack.severity, "")
        self.assertFalse(stack.deployable)

    def test_retour_de_la_stack_la_rend_presente(self):
        """Rien n'est définitif : une stack redéployée reprend sa ligne."""
        store(self.machine, self._rapport("2026-08-11T11:00:00Z", []))
        store(self.machine, self._rapport("2026-08-11T12:00:00Z", RAPPORT["stacks"]))
        self.assertTrue(Stack.objects.get(project="immich").present)

    def test_sonde_sans_cle_stacks_ne_reconcilie_rien(self):
        """« Aucune stack » et « je ne parle pas de stacks » sont deux documents."""
        sans_cle = {k: v for k, v in RAPPORT.items() if k != "stacks"}
        store(self.machine, {**sans_cle, "at": "2026-08-11T11:00:00Z"})
        self.assertTrue(Stack.objects.get(project="immich").present)

    def test_les_autres_machines_ne_sont_pas_touchees(self):
        """La réconciliation est bornée à la machine qui rapporte."""
        autre = _machine(nom="hermes", ip="10.10.0.11")
        store(autre, RAPPORT)
        store(self.machine, self._rapport("2026-08-11T11:00:00Z", []))
        self.assertTrue(Stack.objects.get(machine=autre).present)

    def test_deploiement_refuse_pour_une_absente(self):
        """La console ne demande pas la mise à jour d'une stack qui n'est plus là."""
        store(self.machine, self._rapport("2026-08-11T11:00:00Z", []))
        with mock.patch("apps.fleet.ntfy.requests.post") as poste:
            erreur = ntfy.publish_deploy("selene", "immich")
        self.assertIn("pas une stack connue", erreur)
        poste.assert_not_called()


class StacksPageDisparuesTest(TestCase):
    """Ce que la page fait des stacks disparues : les montrer sans les compter."""

    def setUp(self):
        self.machine = _machine()
        casse = {**RAPPORT["stacks"][0], "compose": "missing"}
        store(self.machine, {**RAPPORT, "stacks": [casse]})
        _admin()
        self.client.login(username="admin", password="motdepasse")

    def _page(self):
        # wud est mocké : la page l'interroge en HTTP, ce qui n'a rien à faire ici.
        with mock.patch("apps.fleet.state.wud.containers", return_value=([], None)):
            return self.client.get(reverse("fleet:stacks"))

    def test_alerte_presente_tant_que_la_stack_est_rapportee(self):
        """Le cas légitime reste alarmé : les conteneurs tournent, le compose manque."""
        self.assertEqual(len(self._page().context["stack_alerts"]), 1)

    def test_alerte_eteinte_quand_la_stack_disparait(self):
        """C'est tout le sujet : l'alerte s'éteint d'elle-même au rapport suivant."""
        store(self.machine, {**RAPPORT, "at": "2026-08-11T11:00:00Z", "stacks": []})
        contexte = self._page().context
        self.assertEqual(contexte["stack_alerts"], [])
        self.assertEqual(contexte["stacks_absentes"], 1)
        # Comptée nulle part ailleurs : annoncer un retard git sur une stack qui
        # n'existe plus serait annoncer un travail à faire qui n'en est pas un.
        self.assertEqual(contexte["stacks_total"], 0)
        self.assertEqual(contexte["stacks_git_en_retard"], 0)


class AcquittementAlerteTest(TestCase):
    """L'alerte que la console ne peut pas réparer, et le seul geste honnête sur elle.

    Une stack qui tourne, dépôt propre et à jour, dont la sonde ne reconnaît pas le
    fichier compose : le remède est dans `home-server-stacks`, pas ici. Restait un encart
    rouge permanent — et une alerte qu'on ne peut pas éteindre cesse d'être lue.
    """

    def setUp(self):
        self.machine = _machine()
        casse = {**RAPPORT["stacks"][0], "compose": "missing"}
        store(self.machine, {**RAPPORT, "stacks": [casse]})
        self.stack = Stack.objects.get(project="immich")
        self.url = reverse("fleet:ack_stack_alert", args=[self.stack.pk])
        self.client = Client()

    def _staff(self):
        _admin()
        self.client.login(username="admin", password="motdepasse")

    def _page(self):
        with mock.patch("apps.fleet.state.wud.containers", return_value=([], None)):
            return self.client.get(reverse("fleet:stacks"))

    def test_anonyme_redirige(self):
        """Un anonyme est renvoyé vers la connexion."""
        self.assertEqual(self.client.post(self.url).status_code, 302)

    def test_utilisateur_sans_droit_interdit(self):
        """Un membre sans droit console reçoit un 403."""
        User.objects.create_user(username="simple", password="motdepasse")
        self.client.login(username="simple", password="motdepasse")
        self.assertEqual(self.client.post(self.url).status_code, 403)

    def test_get_refuse(self):
        """Seul POST est accepté."""
        self._staff()
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_acquittement_eteint_l_alerte(self):
        """La ligne reste, l'état reste affiché, seule l'alerte se tait."""
        self._staff()
        self.assertEqual(len(self._page().context["stack_alerts"]), 1)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 303)
        self.stack.refresh_from_db()
        self.assertEqual(self.stack.alert_ack, "missing")
        self.assertTrue(self.stack.alerte_acquittee)
        # Plus d'encart, plus de ligne rouge, mais l'état lui-même est inchangé. Il
        # reste `warning` : le rapport porte `behind: 2`, et un acquittement ne parle
        # que du compose — le retard git n'a été acquitté par personne.
        self.assertEqual(self.stack.severity, "warning")
        self.assertEqual(self.stack.compose, "missing")

        contexte = self._page().context
        self.assertEqual(contexte["stack_alerts"], [])
        # Comptée, car taire n'est pas effacer.
        self.assertEqual(contexte["stacks_acquittees"], 1)

    def test_second_clic_reactive(self):
        """Un même bouton fait les deux sens : se tromper coûte un autre clic."""
        self._staff()
        self.client.post(self.url)
        self.client.post(self.url)
        self.stack.refresh_from_db()
        self.assertEqual(self.stack.alert_ack, "")
        self.assertEqual(self.stack.severity, "danger")

    def test_un_autre_etat_reveille_l_alerte(self):
        """L'acquittement ne vaut que pour l'état acquitté.

        C'est ce qui le rend auto-nettoyant, et ce qu'un booléen ne pouvait pas faire :
        il aurait masqué le problème suivant, différent, survenu depuis.
        """
        self._staff()
        self.client.post(self.url)
        autre = {**RAPPORT["stacks"][0], "compose": "untracked"}
        store(self.machine, {**RAPPORT, "at": "2026-08-11T11:00:00Z", "stacks": [autre]})
        stack = Stack.objects.get(project="immich")
        self.assertFalse(stack.alerte_acquittee)
        self.assertEqual(stack.severity, "danger")

    def test_retour_a_la_normale_ne_laisse_pas_d_alerte(self):
        """Un compose revenu suivi ne porte plus d'alerte, acquittée ou non."""
        self._staff()
        self.client.post(self.url)
        store(self.machine, {**RAPPORT, "at": "2026-08-11T11:00:00Z"})
        stack = Stack.objects.get(project="immich")
        self.assertFalse(stack.alerte_acquittee)
        self.assertFalse(stack.compose_en_faute)
        # `behind: 2` dans le rapport : la gravité restante est celle du retard git,
        # qui n'a jamais été acquittée — un acquittement ne parle que du compose.
        self.assertEqual(stack.severity, "warning")

    def test_stack_saine_refusee(self):
        """Il n'y a rien à taire sur une stack qui ne signale rien."""
        self._staff()
        store(self.machine, {**RAPPORT, "at": "2026-08-11T11:00:00Z"})
        self.client.post(self.url)
        self.assertEqual(Stack.objects.get(project="immich").alert_ack, "")

    def test_stack_disparue_refusee(self):
        """Une stack qui n'est plus rapportée a son propre bouton, « Oublier »."""
        self._staff()
        store(self.machine, {**RAPPORT, "at": "2026-08-11T11:00:00Z", "stacks": []})
        self.client.post(self.url)
        self.assertEqual(Stack.objects.get(project="immich").alert_ack, "")

    def test_le_bouton_est_propose_au_staff(self):
        """Le geste doit être visible sur la page, sinon il n'existe pas."""
        self._staff()
        self.assertContains(self._page(), "Ignorer l'alerte")
        self.client.post(self.url)
        self.assertContains(self._page(), "Réactiver l'alerte")


class SuppressionStackTest(TestCase):
    """La seule suppression de la console, et elle ne pose aucune condition.

    Les cas visés n'ont de remède nulle part ailleurs : un refactor qui déplace une stack,
    un déménagement entre deux serveurs, une stack de bricolage qu'on ne veut pas suivre
    dans la durée. Rien n'est touché sur la machine — ce qui part est la trace.
    """

    def setUp(self):
        self.machine = _machine()
        store(self.machine, RAPPORT)
        self.stack = Stack.objects.get(project="immich")
        self.url = reverse("fleet:delete_stack", args=[self.stack.pk])
        self.client = Client()

    def _staff(self):
        _admin()
        self.client.login(username="admin", password="motdepasse")

    def _absente(self):
        """Rend la stack absente du dernier rapport."""
        store(self.machine, {**RAPPORT, "at": "2026-08-11T11:00:00Z", "stacks": []})

    def _page(self):
        with mock.patch("apps.fleet.state.wud.containers", return_value=([], None)):
            return self.client.get(reverse("fleet:stacks"))

    def test_anonyme_redirige(self):
        """Un anonyme est renvoyé vers la connexion."""
        self.assertEqual(self.client.post(self.url).status_code, 302)

    def test_utilisateur_sans_droit_interdit(self):
        """Un membre sans droit console reçoit un 403."""
        User.objects.create_user(username="simple", password="motdepasse")
        self.client.login(username="simple", password="motdepasse")
        self.assertEqual(self.client.post(self.url).status_code, 403)

    def test_get_refuse(self):
        """Seul POST est accepté : une suppression n'est pas une lecture."""
        self._staff()
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_suppression_d_une_stack_disparue(self):
        """Le cas du refactor : la ligne part, et elle ne reviendra pas."""
        self._absente()
        self._staff()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], reverse("fleet:stacks"))
        self.assertFalse(Stack.objects.filter(pk=self.stack.pk).exists())

    def test_suppression_d_une_stack_encore_rapportee(self):
        """Aucune condition : une stack vivante se supprime aussi.

        Elle reviendra au prochain rapport — c'est un fait sur la machine, pas une erreur
        de manipulation, donc la page le dit au lieu de refuser le geste.
        """
        self._staff()
        self.client.post(self.url)
        self.assertFalse(Stack.objects.filter(pk=self.stack.pk).exists())

    def test_la_ligne_quitte_la_page(self):
        """Ce que l'on voulait : plus de ligne, et plus rien dans les compteurs."""
        self._staff()
        self.client.post(self.url)
        contexte = self._page().context
        self.assertEqual(contexte["machines"], [])
        self.assertEqual(contexte["stacks_total"], 0)
        self.assertEqual(contexte["stack_alerts"], [])

    def test_rien_n_est_touche_ailleurs(self):
        """La machine et ses rapports restent : la console ne supprime que sa trace."""
        self._staff()
        self.client.post(self.url)
        self.assertTrue(Machine.objects.filter(name="selene").exists())
        self.assertTrue(self.machine.reports.exists())

    def test_suppression_en_masse_des_disparues(self):
        """Un ménage dans le lab en laisse plusieurs : un seul clic les efface."""
        self._absente()
        self._staff()
        response = self.client.post(reverse("fleet:delete_gone_stacks"))
        self.assertEqual(response.status_code, 303)
        self.assertEqual(Stack.objects.count(), 0)

    def test_suppression_en_masse_epargne_les_presentes(self):
        """Le bouton du bandeau ne parle que des disparues : ce qui tourne reste."""
        self._staff()
        self.client.post(reverse("fleet:delete_gone_stacks"))
        self.assertTrue(Stack.objects.filter(pk=self.stack.pk).exists())

    def test_le_bouton_est_propose_sur_chaque_ligne(self):
        """Sur toutes les lignes, pas seulement les disparues."""
        self._staff()
        self.assertContains(self._page(), "Supprimer")


class RetardStackTest(TestCase):
    """Les deux retards, git et images, restent distincts."""

    def setUp(self):
        self.machine = _machine()

    def test_retard_git(self):
        """`behind` distingue « à jour », « en retard » et « on ne sait pas »."""
        store(self.machine, RAPPORT)
        self.assertTrue(Stack.objects.get(project="immich").git_en_retard)

        payload = {**RAPPORT, "stacks": [{**RAPPORT["stacks"][0], "behind": "0"}]}
        store(self.machine, payload)
        self.assertFalse(Stack.objects.get(project="immich").git_en_retard)

        payload = {**RAPPORT, "stacks": [{**RAPPORT["stacks"][0], "behind": "-"}]}
        store(self.machine, payload)
        self.assertIsNone(Stack.objects.get(project="immich").git_en_retard)

    def test_images_appariees_par_label_compose(self):
        """Le label compose de wud gagne sur le nom du conteneur."""
        store(self.machine, RAPPORT)
        stacks = list(Stack.objects.all())
        conteneurs = [
            {"container": "surnom-force", "project": "immich", "image": "immich/server",
             "tag": "v1.0", "available": "v1.1", "update": True},
        ]
        _attacher_images(stacks, conteneurs)
        self.assertEqual(len(stacks[0].images["behind"]), 1)
        self.assertEqual(stacks[0].images["total"], 1)

    def test_images_appariees_par_prefixe_du_nom(self):
        """Sans label, le préfixe du nom sert, projet le plus long d'abord."""
        Stack.objects.create(machine=self.machine, project="immich", path="/a")
        Stack.objects.create(machine=self.machine, project="immich-ml", path="/b")
        stacks = list(Stack.objects.order_by("project"))
        conteneurs = [
            {"container": "immich-machine-learning-1", "project": "", "image": "i",
             "tag": "1", "available": "2", "update": True},
            {"container": "immich-ml-worker-1", "project": "", "image": "i",
             "tag": "1", "available": "2", "update": False},
        ]
        _attacher_images(stacks, conteneurs)
        par_projet = {s.project: s.images for s in stacks}
        # `immich-ml-worker-1` appartient au projet le plus long qui préfixe son nom.
        self.assertEqual(par_projet["immich-ml"]["total"], 1)
        self.assertEqual(par_projet["immich"]["total"], 1)
        self.assertEqual(len(par_projet["immich"]["behind"]), 1)

    def test_conteneur_hors_stack_ignore(self):
        """Un conteneur qui n'appartient à aucune stack connue n'est attribué à personne."""
        Stack.objects.create(machine=self.machine, project="immich", path="/a")
        stacks = list(Stack.objects.all())
        conteneurs = [
            {"container": "wud", "project": "", "image": "wud",
             "tag": "1", "available": "2", "update": True},
        ]
        _attacher_images(stacks, conteneurs)
        self.assertEqual(stacks[0].images["total"], 0)


class WudGroupementTest(TestCase):
    """Le regroupement de la réponse de wud."""

    BRUT = [
        {"name": "immich-server-1", "watcher": "local", "updateAvailable": True,
         "image": {"name": "immich/server", "tag": {"value": "v1.0"}},
         "result": {"tag": "v1.1"},
         "labels": {"com.docker.compose.project": "immich"}},
        {"name": "gatus-1", "watcher": "hermes", "updateAvailable": False,
         "image": {"name": "gatus", "tag": {"value": "v5"}}},
    ]

    def test_watcher_local_est_selene(self):
        """wud nomme `local` le watcher de sa propre socket."""
        groupes = wud.by_container(self.BRUT)
        self.assertIn("selene", groupes)
        self.assertIn("hermes", groupes)

    def test_resume_par_machine(self):
        """Le résumé compte tous les conteneurs et liste ceux en retard."""
        resume = wud.by_machine(self.BRUT)
        self.assertEqual(resume["selene"]["total"], 1)
        self.assertEqual(len(resume["selene"]["behind"]), 1)
        self.assertEqual(resume["hermes"]["behind"], [])

    def test_projet_lu_dans_les_labels(self):
        """Le projet compose vient des labels quand wud les expose."""
        groupes = wud.by_container(self.BRUT)
        self.assertEqual(groupes["selene"][0]["project"], "immich")
        self.assertEqual(groupes["hermes"][0]["project"], "")


@override_settings(FLEET_NTFY_TOKEN="jeton", FLEET_NTFY_URL="http://ntfy.test",
                   FLEET_NTFY_TOPIC="sujet")
class PublicationDeploiementTest(TestCase):
    """`publish_deploy` valide tout en base avant de publier quoi que ce soit."""

    def setUp(self):
        self.machine = _machine()
        store(self.machine, RAPPORT)

    def test_publication_nominale(self):
        """Le corps publié est le verbe et deux noms, jamais un chemin."""
        with mock.patch("apps.fleet.ntfy.requests.post") as poste:
            self.assertIsNone(ntfy.publish_deploy("selene", "immich"))
        corps = poste.call_args.kwargs["data"].decode()
        self.assertEqual(corps, "deploy selene immich")
        self.assertNotIn("/srv", corps)

    def test_machine_inconnue_refusee(self):
        """Une machine hors inventaire ne donne aucune publication."""
        with mock.patch("apps.fleet.ntfy.requests.post") as poste:
            erreur = ntfy.publish_deploy("../../etc", "immich")
        self.assertIn("inventaire", erreur)
        poste.assert_not_called()

    def test_stack_inconnue_refusee(self):
        """Un projet qui n'est pas une stack de cette machine est refusé."""
        with mock.patch("apps.fleet.ntfy.requests.post") as poste:
            erreur = ntfy.publish_deploy("selene", "inexistante")
        self.assertIn("pas une stack connue", erreur)
        poste.assert_not_called()

    def test_stack_sans_script_refusee(self):
        """Sans script rapporté, la console ne demande rien."""
        Stack.objects.filter(project="immich").update(deploy_script="")
        with mock.patch("apps.fleet.ntfy.requests.post") as poste:
            erreur = ntfy.publish_deploy("selene", "immich")
        self.assertIn("script de déploiement", erreur)
        poste.assert_not_called()

    @override_settings(FLEET_NTFY_TOKEN="")
    def test_jeton_absent_refuse(self):
        """Un jeton non configuré ne doit pas se lire « aucun jeton requis »."""
        with mock.patch("apps.fleet.ntfy.requests.post") as poste:
            erreur = ntfy.publish_deploy("selene", "immich")
        self.assertIn("NTFY_TOKEN", erreur)
        poste.assert_not_called()


class DeployStackViewTest(TestCase):
    """L'endpoint de demande de mise à jour d'une stack."""

    def setUp(self):
        self.machine = _machine()
        store(self.machine, RAPPORT)
        self.url = reverse("fleet:deploy", args=["selene", "immich"])
        self.client = Client()

    def test_anonyme_redirige(self):
        """Un anonyme est renvoyé vers la connexion."""
        self.assertEqual(self.client.post(self.url).status_code, 302)

    def test_utilisateur_sans_droit_interdit(self):
        """Un membre sans droit console reçoit un 403."""
        User.objects.create_user(username="simple", password="motdepasse")
        self.client.login(username="simple", password="motdepasse")
        self.assertEqual(self.client.post(self.url).status_code, 403)

    def test_get_refuse(self):
        """Seul POST est accepté : ce n'est pas une action idempotente."""
        _admin()
        self.client.login(username="admin", password="motdepasse")
        self.assertEqual(self.client.get(self.url).status_code, 405)

    @override_settings(FLEET_NTFY_TOKEN="jeton")
    def test_staff_publie_et_revient_en_303(self):
        """Le staff publie, et revient sur la page des stacks en 303."""
        _admin()
        self.client.login(username="admin", password="motdepasse")
        with mock.patch("apps.fleet.ntfy.requests.post"):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 303)
        # Pas de marqueur dans l'URL : la page se recharge parce que le serveur
        # déclare `attente_active`, pas parce qu'un paramètre le lui dit.
        self.assertEqual(response["Location"], reverse("fleet:stacks"))

    @override_settings(FLEET_NTFY_TOKEN="jeton")
    def test_la_demande_est_horodatee(self):
        """Une demande publiée marque la stack « en cours », et pas avant d'être partie."""
        _admin()
        self.client.login(username="admin", password="motdepasse")
        stack = Stack.objects.get(project="immich")
        self.assertIsNone(stack.deploy_requested_at)
        self.assertFalse(stack.deploiement_en_cours)
        with mock.patch("apps.fleet.ntfy.requests.post"):
            self.client.post(self.url)
        stack.refresh_from_db()
        self.assertIsNotNone(stack.deploy_requested_at)
        self.assertTrue(stack.deploiement_en_cours)

    def test_publication_refusee_ne_marque_rien(self):
        """Sans jeton rien n'est publié, donc rien n'est « en cours ».

        L'ordre compte : marquer la ligne avant la publication ferait mentir la page
        dans le seul cas où elle doit être crue.
        """
        _admin()
        self.client.login(username="admin", password="motdepasse")
        with override_settings(FLEET_NTFY_TOKEN=""):
            self.client.post(self.url)
        self.assertIsNone(Stack.objects.get(project="immich").deploy_requested_at)

    @override_settings(FLEET_NTFY_TOKEN="jeton")
    def test_un_rapport_solde_le_en_cours(self):
        """Un rapport arrivé après la demande éteint le badge, quoi qu'ait fait le script.

        C'est ce qui rend le champ auto-nettoyant : l'ingestion n'a rien à remettre à
        zéro, et un déploiement échoué cesse d'être « en cours » dès que la machine
        reparle.
        """
        _admin()
        self.client.login(username="admin", password="motdepasse")
        with mock.patch("apps.fleet.ntfy.requests.post"):
            self.client.post(self.url)
        store(self.machine, RAPPORT)
        self.assertFalse(Stack.objects.get(project="immich").deploiement_en_cours)

    @override_settings(FLEET_NTFY_TOKEN="jeton")
    def test_un_rapport_suit_la_demande(self):
        """Deux messages partent : la demande, puis un rapport.

        L'agent de la machine traite le sujet en série, donc ce second message ne
        s'exécute qu'une fois le déploiement terminé. C'est lui qui fait bouger la ligne
        sans attendre le rapport horaire — l'action partait déjà, c'est la page qui ne
        le montrait pas.
        """
        _admin()
        self.client.login(username="admin", password="motdepasse")
        with mock.patch("apps.fleet.ntfy.requests.post") as poste:
            self.client.post(self.url)
        corps = [appel.kwargs["data"].decode() for appel in poste.call_args_list]
        self.assertEqual(corps, ["deploy selene immich", "report selene"])


@override_settings(FLEET_NTFY_TOKEN="jeton")
class ApproveViewRetourTest(TestCase):
    """Le rafraîchissement forcé, et où il ramène.

    `retour` est une liste blanche de deux noms de vues, pas une URL : un paramètre de
    redirection libre serait une redirection ouverte, et il n'y a que deux destinations
    à connaître.
    """

    def setUp(self):
        _machine()
        self.url = reverse("fleet:approve", args=["selene", "report"])
        self.client = Client()
        _admin()
        self.client.login(username="admin", password="motdepasse")

    def _poste(self, **data):
        with mock.patch("apps.fleet.ntfy.requests.post"):
            return self.client.post(self.url, data)

    def test_retour_sur_les_stacks(self):
        """Rafraîchir depuis la page Stacks y ramène."""
        response = self._poste(retour="fleet:stacks")
        self.assertEqual(response["Location"], reverse("fleet:stacks"))

    def test_retour_par_defaut(self):
        """Sans champ `retour`, on revient sur la page Machines."""
        self.assertEqual(self._poste()["Location"], reverse("fleet:index"))

    def test_retour_hors_liste_ignore(self):
        """Une destination inventée est ignorée, pas suivie."""
        response = self._poste(retour="https://exemple.invalide/pwned")
        self.assertEqual(response["Location"], reverse("fleet:index"))

    def test_report_ne_publie_pas_de_rapport_de_suivi(self):
        """`report` est déjà un rapport : pas de second message."""
        with mock.patch("apps.fleet.ntfy.requests.post") as poste:
            self.client.post(self.url, {"retour": "fleet:stacks"})
        corps = [appel.kwargs["data"].decode() for appel in poste.call_args_list]
        self.assertEqual(corps, ["report selene"])


@override_settings(FLEET_NTFY_TOKEN="jeton")
class ActionEnCoursTest(TestCase):
    """Ce qui permet à la page de dire « il se passe quelque chose », et de l'attendre.

    C'est le manque qui a fait passer un `upgrade` de hecate pour une action ignorée :
    il a duré quatorze minutes, la page n'en montrait rien, et le rechargement
    automatique — un nombre de tours fixe, à l'époque — avait renoncé bien avant.
    """

    def setUp(self):
        self.machine = _machine(nom="hecate", ip="10.10.10.13")
        self.url = reverse("fleet:approve", args=["hecate", "upgrade"])
        self.client = Client()
        _admin()
        self.client.login(username="admin", password="motdepasse")

    def _approuve(self):
        with mock.patch("apps.fleet.ntfy.requests.post"):
            self.client.post(self.url)
        self.machine.refresh_from_db()

    def test_action_publiee_marque_la_machine(self):
        """Le verbe et l'heure sont retenus, pour que la page puisse les afficher."""
        self.assertFalse(self.machine.action_en_cours)
        self._approuve()
        self.assertEqual(self.machine.action_requested_verb, "upgrade")
        self.assertTrue(self.machine.action_en_cours)

    def test_publication_refusee_ne_marque_rien(self):
        """Sans jeton rien n'est publié, donc rien n'est « en cours »."""
        with override_settings(FLEET_NTFY_TOKEN=""):
            with mock.patch("apps.fleet.ntfy.requests.post"):
                self.client.post(self.url)
        self.machine.refresh_from_db()
        self.assertIsNone(self.machine.action_requested_at)

    def test_un_rapport_solde_l_action(self):
        """Un rapport reçu après la demande éteint le badge, réussie ou non.

        C'est ce qui rend les deux champs auto-nettoyants : l'ingestion n'a rien à
        remettre à zéro, et une action ratée cesse d'être « en cours » dès que la machine
        reparle.
        """
        self._approuve()
        store(self.machine, RAPPORT)
        self.machine.refresh_from_db()
        self.assertFalse(self.machine.action_en_cours)

    def test_la_page_declare_l_attente(self):
        """`attente_active` est ce qui fait recharger la page, et il vient du serveur."""
        page = reverse("fleet:index")
        self.assertFalse(self.client.get(page).context["attente_active"])
        self._approuve()
        self.assertTrue(self.client.get(page).context["attente_active"])
        store(self.machine, RAPPORT)
        self.assertFalse(self.client.get(page).context["attente_active"])
