"""test.py"""
import datetime

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from common.user_utils import ENREGISTRE, AUTORISE, AVANCE, ADMINISTRATEUR, get_user_level
from .models import ProjetCategorie, Projet


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


class ProjetsAccessTest(TestCase):
    """Tests d'accès aux pages projets."""

    def setUp(self):
        self.categorie = ProjetCategorie.objects.create(
            nom="Logiciel", slug="logiciel")
        self.projet_actif = Projet.objects.create(
            titre="Projet A", slug="projet-a", categorie=self.categorie,
            resume="Un résumé", date_creation=datetime.date(2025, 1, 1), actif=True)
        self.projet_inactif = Projet.objects.create(
            titre="Projet B", slug="projet-b", categorie=self.categorie,
            resume="Un résumé", date_creation=datetime.date(2025, 1, 1), actif=False)
        self.client = Client()

    def test_mes_projets_returns_200(self):
        response = self.client.get(reverse("mes_projets"))
        self.assertEqual(response.status_code, 200)

    def test_mes_projets_categorie_returns_200(self):
        response = self.client.get(reverse("mes_projets_categorie", args=["logiciel"]))
        self.assertEqual(response.status_code, 200)

    def test_mes_projets_detail_actif_returns_200(self):
        response = self.client.get(reverse("mes_projets_detail", args=["projet-a"]))
        self.assertEqual(response.status_code, 200)

    def test_mes_projets_detail_inactif_returns_404(self):
        response = self.client.get(reverse("mes_projets_detail", args=["projet-b"]))
        self.assertEqual(response.status_code, 404)

    def test_mes_projets_categorie_inexistante_returns_404(self):
        response = self.client.get(reverse("mes_projets_categorie", args=["inexistant"]))
        self.assertEqual(response.status_code, 404)


class ProjetsTemplatesTest(TestCase):
    """Tests des templates utilisés pour les projets."""

    def setUp(self):
        self.categorie = ProjetCategorie.objects.create(
            nom="Logiciel", slug="logiciel")
        self.projet = Projet.objects.create(
            titre="Projet A", slug="projet-a", categorie=self.categorie,
            resume="Un résumé", date_creation=datetime.date(2025, 1, 1), actif=True)

    def test_mes_projets_uses_correct_template(self):
        response = self.client.get(reverse("mes_projets"))
        self.assertTemplateUsed(response, "www/mes_projets.html")

    def test_mes_projets_categorie_uses_correct_template(self):
        response = self.client.get(reverse("mes_projets_categorie", args=["logiciel"]))
        self.assertTemplateUsed(response, "www/mes_projets_categorie.html")

    def test_mes_projets_detail_uses_correct_template(self):
        response = self.client.get(reverse("mes_projets_detail", args=["projet-a"]))
        self.assertTemplateUsed(response, "www/mes_projets_detail.html")


class AdminProjetsAccessTest(TestCase):
    """Tests d'accès à la gestion des projets."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.admin = User.objects.create_user(username="adminuser", password="adminpass")
        self.admin.userprofile.user_level = ADMINISTRATEUR
        self.admin.userprofile.save()
        self.categorie = ProjetCategorie.objects.create(
            nom="Logiciel", slug="logiciel")
        self.client = Client()

    def test_admin_projets_anonymous_redirects(self):
        response = self.client.get(reverse("admin_projets"))
        self.assertEqual(response.status_code, 302)

    def test_admin_projets_regular_user_forbidden(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("admin_projets"))
        self.assertEqual(response.status_code, 403)

    def test_admin_projets_admin_returns_200(self):
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(reverse("admin_projets"))
        self.assertEqual(response.status_code, 200)

    def test_admin_projet_ajouter_post(self):
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_projet_ajouter"), {
            "titre": "Nouveau Projet",
            "categorie": self.categorie.pk,
            "resume": "Un résumé court",
            "contenu": "",
            "lien_externe": "",
            "mdi_icon_name": "",
            "icone_url": "",
            "couleur": "#5090C1",
            "date_creation": "2025-06-01",
            "actif": True,
            "visibilite": -1,
            "ordre": 1,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Projet.objects.filter(slug="nouveau-projet").exists())

    def test_admin_projet_supprimer_post(self):
        projet = Projet.objects.create(
            titre="Temp", slug="temp", categorie=self.categorie,
            resume="Temp", date_creation=datetime.date(2025, 1, 1))
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_projet_supprimer", args=[projet.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Projet.objects.filter(pk=projet.pk).exists())

    def test_admin_projet_categorie_ajouter_post(self):
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_projet_categorie_ajouter"), {
            "nom": "Hardware",
            "mdi_icon_name": "",
            "ordre": 1,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ProjetCategorie.objects.filter(slug="hardware").exists())

    def test_admin_projet_categorie_modifier_post(self):
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(
            reverse("admin_projet_categorie_modifier", args=[self.categorie.pk]), {
                "nom": "Logiciel modifié",
                "mdi_icon_name": "",
                "ordre": 1,
            })
        self.assertEqual(response.status_code, 302)
        self.categorie.refresh_from_db()
        self.assertEqual(self.categorie.nom, "Logiciel modifié")

    def test_admin_projet_categorie_supprimer_post(self):
        cat = ProjetCategorie.objects.create(nom="Temp", slug="temp-cat")
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_projet_categorie_supprimer", args=[cat.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ProjetCategorie.objects.filter(pk=cat.pk).exists())


class ProjetIconeTest(TestCase):
    """Tests du système d'icône multi-mode des projets."""

    def setUp(self):
        self.categorie = ProjetCategorie.objects.create(
            nom="Test", slug="test")

    def _make_projet(self, **kwargs):
        """Crée un projet avec les paramètres donnés."""
        defaults = {
            "titre": "Projet Test",
            "slug": "projet-test",
            "categorie": self.categorie,
            "resume": "Un résumé",
            "date_creation": datetime.date(2025, 1, 1),
        }
        defaults.update(kwargs)
        return Projet.objects.create(**defaults)

    def test_projet_icone_html_mdi(self):
        """Vérifie le HTML d'une icône MDI."""
        projet = self._make_projet(mdi_icon_name="code-tags")
        html = projet.icone_html()
        self.assertIn("mdi-code-tags", html)
        self.assertIn("<span", html)

    def test_projet_icone_html_url(self):
        """Vérifie le HTML d'une icône URL."""
        projet = self._make_projet(icone_url="https://example.com/icon.png")
        html = projet.icone_html()
        self.assertIn("<img", html)
        self.assertIn("https://example.com/icon.png", html)
        self.assertIn("projet-icone-img", html)

    def test_projet_icone_html_vide(self):
        """Vérifie le retour vide sans icône."""
        projet = self._make_projet()
        self.assertEqual(projet.icone_html(), "")

    def test_projet_has_icone(self):
        """Vérifie le booléen has_icone."""
        projet_vide = self._make_projet(slug="vide")
        self.assertFalse(projet_vide.has_icone())
        projet_mdi = self._make_projet(slug="mdi", mdi_icon_name="star")
        self.assertTrue(projet_mdi.has_icone())
        projet_url = self._make_projet(slug="url", icone_url="https://example.com/i.png")
        self.assertTrue(projet_url.has_icone())

    def test_projet_creation_avec_url_icone(self):
        """Vérifie la création d'un projet avec icone_url via admin."""
        admin = User.objects.create_user(username="adminuser", password="adminpass")
        admin.userprofile.user_level = ADMINISTRATEUR
        admin.userprofile.save()
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_projet_ajouter"), {
            "titre": "Projet URL",
            "categorie": self.categorie.pk,
            "resume": "Résumé",
            "contenu": "",
            "lien_externe": "",
            "mdi_icon_name": "",
            "icone_url": "https://example.com/icon.png",
            "couleur": "#5090C1",
            "date_creation": "2025-06-01",
            "actif": True,
            "visibilite": -1,
            "ordre": 1,
        })
        self.assertEqual(response.status_code, 302)
        projet = Projet.objects.get(slug="projet-url")
        self.assertEqual(projet.icone_url, "https://example.com/icon.png")

    def test_projet_validation_multiple_modes(self):
        """Vérifie que MDI + URL simultanés génèrent une erreur."""
        admin = User.objects.create_user(username="adminuser2", password="adminpass")
        admin.userprofile.user_level = ADMINISTRATEUR
        admin.userprofile.save()
        self.client.login(username="adminuser2", password="adminpass")
        response = self.client.post(reverse("admin_projet_ajouter"), {
            "titre": "Projet Double",
            "categorie": self.categorie.pk,
            "resume": "Résumé",
            "contenu": "",
            "lien_externe": "",
            "mdi_icon_name": "star",
            "icone_url": "https://example.com/icon.png",
            "couleur": "#5090C1",
            "date_creation": "2025-06-01",
            "actif": True,
            "visibilite": -1,
            "ordre": 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Projet.objects.filter(slug="projet-double").exists())


class ProjetVisibiliteTest(TestCase):
    """Tests du filtrage des projets par visibilité."""

    def setUp(self):
        self.categorie = ProjetCategorie.objects.create(
            nom="Logiciel", slug="logiciel")
        self.projet_public = Projet.objects.create(
            titre="Public", slug="public", categorie=self.categorie,
            resume="Résumé", date_creation=datetime.date(2025, 1, 1),
            actif=True, visibilite=-1)
        self.projet_enregistre = Projet.objects.create(
            titre="Enregistré", slug="enregistre", categorie=self.categorie,
            resume="Résumé", date_creation=datetime.date(2025, 1, 1),
            actif=True, visibilite=ENREGISTRE)
        self.projet_avance = Projet.objects.create(
            titre="Avancé", slug="avance", categorie=self.categorie,
            resume="Résumé", date_creation=datetime.date(2025, 1, 1),
            actif=True, visibilite=AVANCE)
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user_avance = User.objects.create_user(username="avanceuser", password="testpass")
        self.user_avance.userprofile.user_level = AVANCE
        self.user_avance.userprofile.save()
        self.admin = User.objects.create_user(username="adminuser", password="adminpass")
        self.admin.userprofile.user_level = ADMINISTRATEUR
        self.admin.userprofile.save()
        self.client = Client()

    def test_projet_public_visible_anonyme(self):
        """Un projet public (visibilite=-1) est visible par un anonyme."""
        response = self.client.get(reverse("mes_projets"))
        self.assertEqual(response.status_code, 200)
        categories = response.context["categories"]
        projets = list(categories.first().projets.all())
        slugs = [p.slug for p in projets]
        self.assertIn("public", slugs)

    def test_projet_enregistre_invisible_anonyme(self):
        """Un projet enregistré (visibilite=0) est invisible pour un anonyme."""
        response = self.client.get(reverse("mes_projets"))
        categories = response.context["categories"]
        projets = list(categories.first().projets.all())
        slugs = [p.slug for p in projets]
        self.assertNotIn("enregistre", slugs)

    def test_projet_enregistre_visible_user(self):
        """Un projet enregistré est visible pour un utilisateur connecté."""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("mes_projets"))
        categories = response.context["categories"]
        projets = list(categories.first().projets.all())
        slugs = [p.slug for p in projets]
        self.assertIn("enregistre", slugs)

    def test_projet_avance_invisible_user_normal(self):
        """Un projet avancé est invisible pour un utilisateur enregistré."""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("mes_projets"))
        categories = response.context["categories"]
        projets = list(categories.first().projets.all())
        slugs = [p.slug for p in projets]
        self.assertNotIn("avance", slugs)

    def test_projet_avance_visible_user_avance(self):
        """Un projet avancé est visible pour un utilisateur avancé."""
        self.client.login(username="avanceuser", password="testpass")
        response = self.client.get(reverse("mes_projets"))
        categories = response.context["categories"]
        projets = list(categories.first().projets.all())
        slugs = [p.slug for p in projets]
        self.assertIn("avance", slugs)

    def test_projet_detail_visibilite_404(self):
        """Un accès direct à un projet restreint retourne 404."""
        response = self.client.get(reverse("mes_projets_detail", args=["avance"]))
        self.assertEqual(response.status_code, 404)

    def test_admin_projets_voit_tout(self):
        """La vue admin affiche tous les projets peu importe la visibilité."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(reverse("admin_projets"))
        projets = response.context["projets"]
        slugs = [p.slug for p in projets]
        self.assertIn("public", slugs)
        self.assertIn("enregistre", slugs)
        self.assertIn("avance", slugs)
