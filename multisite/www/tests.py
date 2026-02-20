"""test.py"""
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from common.user_utils import ENREGISTRE, AUTORISE, AVANCE, ADMINISTRATEUR


class PagesAccessTest(TestCase):
    """Tests d'acc\u00e8s aux pages publiques du site."""

    def test_accueil_returns_200(self):
        client = Client()
        response = client.get(reverse("accueil"))
        self.assertEqual(response.status_code, 200)

    def test_a_propos_returns_200(self):
        client = Client()
        response = client.get(reverse("a_propos"))
        self.assertEqual(response.status_code, 200)

    def test_mes_projets_returns_200(self):
        client = Client()
        response = client.get(reverse("mes_projets"))
        self.assertEqual(response.status_code, 200)


class ArchivesAccessTest(TestCase):
    """Tests d'acces aux pages archives et bricolage (niveau avance requis)."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.avance = User.objects.create_user(username="avanceuser", password="testpass")
        self.avance.userprofile.user_level = AVANCE
        self.avance.userprofile.save()
        self.client = Client()

    def test_archives_anonymous_redirects(self):
        response = self.client.get(reverse("archives"))
        self.assertEqual(response.status_code, 302)

    def test_archives_news_anonymous_redirects(self):
        response = self.client.get(reverse("archives_news"))
        self.assertEqual(response.status_code, 302)

    def test_archives_research_anonymous_redirects(self):
        response = self.client.get(reverse("archives_research"))
        self.assertEqual(response.status_code, 302)

    def test_bricolage_anonymous_redirects(self):
        response = self.client.get(reverse("bricolage"))
        self.assertEqual(response.status_code, 302)

    def test_administration_anonymous_redirects(self):
        response = self.client.get(reverse("administration"))
        self.assertEqual(response.status_code, 302)

    def test_archives_regular_user_forbidden(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("archives"))
        self.assertEqual(response.status_code, 403)

    def test_archives_news_regular_user_forbidden(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("archives_news"))
        self.assertEqual(response.status_code, 403)

    def test_archives_research_regular_user_forbidden(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("archives_research"))
        self.assertEqual(response.status_code, 403)

    def test_bricolage_regular_user_forbidden(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("bricolage"))
        self.assertEqual(response.status_code, 403)

    def test_archives_avance_returns_200(self):
        self.client.login(username="avanceuser", password="testpass")
        response = self.client.get(reverse("archives"))
        self.assertEqual(response.status_code, 200)

    def test_archives_news_avance_returns_200(self):
        self.client.login(username="avanceuser", password="testpass")
        response = self.client.get(reverse("archives_news"))
        self.assertEqual(response.status_code, 200)

    def test_archives_research_avance_returns_200(self):
        self.client.login(username="avanceuser", password="testpass")
        response = self.client.get(reverse("archives_research"))
        self.assertEqual(response.status_code, 200)

    def test_bricolage_avance_returns_200(self):
        self.client.login(username="avanceuser", password="testpass")
        response = self.client.get(reverse("bricolage"))
        self.assertEqual(response.status_code, 200)

    def test_administration_regular_user_forbidden(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("administration"))
        self.assertEqual(response.status_code, 403)


class TemplatesTest(TestCase):
    """Tests des templates utilis\u00e9s par les nouvelles pages."""

    def test_accueil_uses_correct_template(self):
        client = Client()
        response = client.get(reverse("accueil"))
        self.assertTemplateUsed(response, "www/accueil.html")

    def test_a_propos_uses_correct_template(self):
        client = Client()
        response = client.get(reverse("a_propos"))
        self.assertTemplateUsed(response, "www/a_propos.html")

    def test_mes_projets_uses_correct_template(self):
        client = Client()
        response = client.get(reverse("mes_projets"))
        self.assertTemplateUsed(response, "www/mes_projets.html")

    def test_bricolage_uses_correct_template(self):
        user = User.objects.create_user(username="testuser", password="testpass")
        user.userprofile.user_level = AVANCE
        user.userprofile.save()
        client = Client()
        client.login(username="testuser", password="testpass")
        response = client.get(reverse("bricolage"))
        self.assertTemplateUsed(response, "www/bricolage.html")

    def test_administration_uses_correct_template(self):
        admin = User.objects.create_user(username="adminuser", password="testpass")
        admin.userprofile.user_level = ADMINISTRATEUR
        admin.userprofile.save()
        client = Client()
        client.login(username="adminuser", password="testpass")
        response = client.get(reverse("administration"))
        self.assertTemplateUsed(response, "www/administration.html")


class AdminUsersAccessTest(TestCase):
    """Tests d'acc\u00e8s \u00e0 la page de gestion des utilisateurs."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.admin = User.objects.create_user(username="adminuser", password="adminpass")
        self.admin.userprofile.user_level = ADMINISTRATEUR
        self.admin.userprofile.save()
        self.client = Client()

    def test_admin_users_anonymous_redirects(self):
        response = self.client.get(reverse("admin_users"))
        self.assertEqual(response.status_code, 302)

    def test_admin_users_regular_user_forbidden(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("admin_users"))
        self.assertEqual(response.status_code, 403)

    def test_admin_users_admin_returns_200(self):
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(reverse("admin_users"))
        self.assertEqual(response.status_code, 200)

    def test_admin_users_change_level(self):
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_users"), {
            "user_id": self.user.pk,
            "user_level": str(AUTORISE),
        })
        self.assertEqual(response.status_code, 302)
        self.user.userprofile.refresh_from_db()
        self.assertEqual(self.user.userprofile.user_level, AUTORISE)

    def test_admin_users_superuser_protected(self):
        superuser = User.objects.create_superuser(
            username="superuser", password="superpass",
        )
        self.client.login(username="adminuser", password="adminpass")
        self.client.post(reverse("admin_users"), {
            "user_id": superuser.pk,
            "user_level": str(ENREGISTRE),
        })
        superuser.userprofile.refresh_from_db()
        self.assertEqual(superuser.userprofile.user_level, ADMINISTRATEUR)


class RemovedPagesTest(TestCase):
    """Tests que les anciennes URLs supprim\u00e9es retournent 404."""

    def test_projects_returns_404(self):
        client = Client()
        response = client.get("/projects")
        self.assertEqual(response.status_code, 404)

    def test_links_returns_404(self):
        client = Client()
        response = client.get("/links")
        self.assertEqual(response.status_code, 404)

    def test_www_returns_404(self):
        client = Client()
        response = client.get("/www/")
        self.assertEqual(response.status_code, 404)

    def test_old_news_returns_404(self):
        client = Client()
        response = client.get("/news/")
        self.assertEqual(response.status_code, 404)

    def test_old_research_returns_404(self):
        client = Client()
        response = client.get("/research/")
        self.assertEqual(response.status_code, 404)
