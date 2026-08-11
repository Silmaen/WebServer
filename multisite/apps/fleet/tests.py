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
        """Le staff publie, et la redirection est un 303."""
        _admin()
        self.client.login(username="admin", password="motdepasse")
        with mock.patch("apps.fleet.ntfy.requests.post"):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], reverse("fleet:stacks"))
