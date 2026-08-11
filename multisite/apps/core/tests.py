"""Tests des accès et du gabarit des pages de la console."""
from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from common.user_utils import ADMINISTRATEUR


def _utilisateur(nom, groupe=None, staff=False):
    """Crée un utilisateur, éventuellement membre d'un groupe de la console.

    `is_staff` passe par `user_level` : `UserProfile.save()` le dérive du niveau, donc
    le poser directement sur le `User` serait écrasé au premier enregistrement.
    """
    user = User.objects.create_user(username=nom, password="motdepasse")
    if staff:
        user.userprofile.user_level = ADMINISTRATEUR
        user.userprofile.save()
        user.refresh_from_db()
    if groupe:
        user.groups.add(Group.objects.get_or_create(name=groupe)[0])
    return user


class ConsoleAccessTest(TestCase):
    """Les trois cas d'accès à une page de la console."""

    def setUp(self):
        _utilisateur("anonyme_ignore")
        _utilisateur("sansgroupe")
        _utilisateur("viewer", groupe="viewers")
        _utilisateur("admin", staff=True)
        self.client = Client()

    def test_anonyme_redirige(self):
        """Un anonyme est redirigé vers la connexion."""
        response = self.client.get(reverse("fleet:index"))
        self.assertEqual(response.status_code, 302)

    def test_connecte_sans_groupe_interdit(self):
        """Un membre du site sans groupe de console reçoit un 403."""
        self.client.login(username="sansgroupe", password="motdepasse")
        response = self.client.get(reverse("fleet:index"))
        self.assertEqual(response.status_code, 403)

    def test_viewer_accede_en_lecture(self):
        """Un membre du groupe viewers accède aux pages de lecture."""
        self.client.login(username="viewer", password="motdepasse")
        self.assertEqual(self.client.get(reverse("fleet:index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("devices:list")).status_code, 200)

    def test_viewer_refuse_sur_une_page_staff(self):
        """Les pages d'écriture restent réservées au staff."""
        self.client.login(username="viewer", password="motdepasse")
        response = self.client.get(reverse("devices:create"))
        self.assertEqual(response.status_code, 403)

    def test_admin_accede_a_tout(self):
        """Le staff accède aussi aux pages d'écriture et d'administration."""
        self.client.login(username="admin", password="motdepasse")
        self.assertEqual(self.client.get(reverse("devices:create")).status_code, 200)
        self.assertEqual(self.client.get(reverse("core:admin-panel")).status_code, 200)


class ConsoleMiddlewareScopeTest(TestCase):
    """Le 403 de la console ne doit jamais toucher le site public."""

    def setUp(self):
        _utilisateur("membre")
        self.client = Client()
        self.client.login(username="membre", password="motdepasse")

    def test_site_public_reste_accessible(self):
        """Un membre sans groupe de console garde accès au site et à son profil."""
        self.assertEqual(self.client.get(reverse("a_propos")).status_code, 200)
        self.assertEqual(self.client.get(reverse("mes_projets")).status_code, 200)
        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)

    def test_console_interdite(self):
        """Seules les URLs de la console sont gardées."""
        self.assertEqual(self.client.get(reverse("fleet:index")).status_code, 403)


class ConsolePageMixinTest(TestCase):
    """Les pages de la console fournissent le contexte du gabarit du site."""

    def setUp(self):
        _utilisateur("admin", staff=True)
        self.client = Client()
        self.client.login(username="admin", password="motdepasse")

    def test_titre_et_navigation_de_la_flotte(self):
        """La page flotte porte son titre, son entrée de menu et sa sous-navigation."""
        response = self.client.get(reverse("fleet:index"))
        self.assertEqual(response.context["page_subtitle"], "Flotte")
        self.assertEqual(response.context["page"], "fleet:index")
        self.assertEqual(response.context["subpage"], "Machines")
        noms = [sp["name"] for sp in response.context["subpages"]]
        self.assertEqual(noms, ["Machines", "Stacks"])

    def test_titre_dependant_de_l_objet(self):
        """Une page de détail titre avec son objet."""
        from apps.devices.models import Device

        appareil = Device.objects.create(hostname="selene", ip_address="10.10.0.10")
        response = self.client.get(reverse("devices:detail", args=[appareil.pk]))
        self.assertEqual(response.context["page_subtitle"], "selene")
        self.assertEqual(response.context["page"], "devices:list")

    def test_aucune_page_ne_titre_console(self):
        """Le titre « Console » générique ne doit plus apparaître."""
        for nom in ("dashboard:index", "fleet:index", "devices:list", "network:list"):
            with self.subTest(page=nom):
                response = self.client.get(reverse(nom))
                self.assertNotEqual(response.context["page_subtitle"], "Console")
                self.assertTrue(response.context["page_subtitle"])


class FleetStacksPageTest(TestCase):
    """La page des stacks, séparée de celle des machines."""

    def setUp(self):
        _utilisateur("admin", staff=True)
        self.client = Client()
        self.client.login(username="admin", password="motdepasse")

    def test_page_accessible_et_gabarit(self):
        """La page répond et utilise son propre gabarit."""
        response = self.client.get(reverse("fleet:stacks"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "fleet/stacks.html")

    def test_sous_page_active(self):
        """La sous-page active est Stacks, sous l'entrée Flotte."""
        response = self.client.get(reverse("fleet:stacks"))
        self.assertEqual(response.context["subpage"], "Stacks")
        self.assertEqual(response.context["page"], "fleet:index")

    def test_machines_sans_stack_sont_ecartees(self):
        """Seules les machines rapportant une stack sont listées."""
        from apps.fleet.models import Machine

        Machine.objects.create(name="sansstack", ip="10.10.0.20")
        response = self.client.get(reverse("fleet:stacks"))
        self.assertEqual(list(response.context["machines"]), [])
