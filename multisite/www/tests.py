"""test.py"""
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse


class PagesAccessTest(TestCase):
    """Tests d'accès aux pages publiques du site."""

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
    """Tests d'accès aux pages archives (authentification requise)."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
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

    def test_archives_authenticated_returns_200(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("archives"))
        self.assertEqual(response.status_code, 200)

    def test_archives_news_authenticated_returns_200(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("archives_news"))
        self.assertEqual(response.status_code, 200)

    def test_archives_research_authenticated_returns_200(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("archives_research"))
        self.assertEqual(response.status_code, 200)

    def test_bricolage_authenticated_returns_200(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("bricolage"))
        self.assertEqual(response.status_code, 200)

    def test_administration_authenticated_returns_200(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("administration"))
        self.assertEqual(response.status_code, 200)


class TemplatesTest(TestCase):
    """Tests des templates utilisés par les nouvelles pages."""

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
        client = Client()
        client.login(username="testuser", password="testpass")
        response = client.get(reverse("bricolage"))
        self.assertTemplateUsed(response, "www/bricolage.html")

    def test_administration_uses_correct_template(self):
        user = User.objects.create_user(username="testuser", password="testpass")
        client = Client()
        client.login(username="testuser", password="testpass")
        response = client.get(reverse("administration"))
        self.assertTemplateUsed(response, "www/administration.html")


class RemovedPagesTest(TestCase):
    """Tests que les anciennes URLs supprimées retournent 404."""

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
