"""test.py"""
import datetime
import socket
import unittest.mock

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse

from common.user_utils import ENREGISTRE, AUTORISE, AVANCE, ADMINISTRATEUR, get_user_level
from .models import ProjetCategorie, Projet, BricolageArticle, ServiceCategorie, Machine, Serveur


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


class BricolageAccessTest(TestCase):
    """Tests d'accès aux pages bricolage."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.avance = User.objects.create_user(username="avanceuser", password="testpass")
        self.avance.userprofile.user_level = AVANCE
        self.avance.userprofile.save()
        self.article = BricolageArticle.objects.create(
            titre="Test Bricolage", slug="test-bricolage",
            contenu="Du contenu", date=datetime.date(2025, 6, 1))
        self.client = Client()

    def test_bricolage_liste_anonymous_redirects(self):
        """Un anonyme est redirigé vers le login."""
        response = self.client.get(reverse("bricolage"))
        self.assertEqual(response.status_code, 302)

    def test_bricolage_liste_regular_user_forbidden(self):
        """Un utilisateur normal reçoit un 403."""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("bricolage"))
        self.assertEqual(response.status_code, 403)

    def test_bricolage_liste_avance_returns_200(self):
        """Un utilisateur avancé accède à la liste."""
        self.client.login(username="avanceuser", password="testpass")
        response = self.client.get(reverse("bricolage"))
        self.assertEqual(response.status_code, 200)

    def test_bricolage_liste_uses_correct_template(self):
        """Vérifie le template de la liste bricolage."""
        self.client.login(username="avanceuser", password="testpass")
        response = self.client.get(reverse("bricolage"))
        self.assertTemplateUsed(response, "www/bricolage.html")

    def test_bricolage_detail_avance_returns_200(self):
        """Un utilisateur avancé accède au détail."""
        self.client.login(username="avanceuser", password="testpass")
        response = self.client.get(reverse("bricolage_detail", args=["test-bricolage"]))
        self.assertEqual(response.status_code, 200)

    def test_bricolage_detail_uses_correct_template(self):
        """Vérifie le template du détail bricolage."""
        self.client.login(username="avanceuser", password="testpass")
        response = self.client.get(reverse("bricolage_detail", args=["test-bricolage"]))
        self.assertTemplateUsed(response, "www/bricolage_detail.html")

    def test_bricolage_detail_inexistant_returns_404(self):
        """Un slug inexistant retourne 404."""
        self.client.login(username="avanceuser", password="testpass")
        response = self.client.get(reverse("bricolage_detail", args=["inexistant"]))
        self.assertEqual(response.status_code, 404)


class AdminBricolagesAccessTest(TestCase):
    """Tests d'accès à la gestion des articles de bricolage."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.admin = User.objects.create_user(username="adminuser", password="adminpass")
        self.admin.userprofile.user_level = ADMINISTRATEUR
        self.admin.userprofile.save()
        self.client = Client()

    def test_admin_bricolages_anonymous_redirects(self):
        """Un anonyme est redirigé vers le login."""
        response = self.client.get(reverse("admin_bricolages"))
        self.assertEqual(response.status_code, 302)

    def test_admin_bricolages_regular_user_forbidden(self):
        """Un utilisateur normal reçoit un 403."""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("admin_bricolages"))
        self.assertEqual(response.status_code, 403)

    def test_admin_bricolages_admin_returns_200(self):
        """Un administrateur accède à la page."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(reverse("admin_bricolages"))
        self.assertEqual(response.status_code, 200)

    def test_admin_bricolage_ajouter_post(self):
        """POST crée un article avec auto-slug."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_bricolage_ajouter"), {
            "titre": "Mon Bricolage",
            "contenu": "Du contenu markdown",
            "date": "2025-06-01",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BricolageArticle.objects.filter(slug="mon-bricolage").exists())

    def test_admin_bricolage_modifier_post(self):
        """POST modifie le titre d'un article."""
        article = BricolageArticle.objects.create(
            titre="Original", slug="original",
            date=datetime.date(2025, 1, 1))
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(
            reverse("admin_bricolage_modifier", args=[article.pk]), {
                "titre": "Modifié",
                "contenu": "",
                "date": "2025-01-01",
            })
        self.assertEqual(response.status_code, 302)
        article.refresh_from_db()
        self.assertEqual(article.titre, "Modifié")

    def test_admin_bricolage_supprimer_post(self):
        """POST supprime un article."""
        article = BricolageArticle.objects.create(
            titre="Temp", slug="temp",
            date=datetime.date(2025, 1, 1))
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_bricolage_supprimer", args=[article.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(BricolageArticle.objects.filter(pk=article.pk).exists())


class MonitoringAccessTest(TestCase):
    """Tests d'accès à la page monitoring (niveau administrateur requis)."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.avance = User.objects.create_user(username="avanceuser", password="testpass")
        self.avance.userprofile.user_level = AVANCE
        self.avance.userprofile.save()
        self.admin = User.objects.create_user(username="adminuser", password="adminpass")
        self.admin.userprofile.user_level = ADMINISTRATEUR
        self.admin.userprofile.save()
        self.client = Client()

    def test_monitoring_anonymous_redirects(self):
        """Un anonyme est redirigé vers le login."""
        response = self.client.get(reverse("monitoring"))
        self.assertEqual(response.status_code, 302)

    def test_monitoring_regular_user_forbidden(self):
        """Un utilisateur normal reçoit un 403."""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("monitoring"))
        self.assertEqual(response.status_code, 403)

    def test_monitoring_avance_user_forbidden(self):
        """Un utilisateur avancé reçoit un 403."""
        self.client.login(username="avanceuser", password="testpass")
        response = self.client.get(reverse("monitoring"))
        self.assertEqual(response.status_code, 403)

    def test_monitoring_admin_returns_200(self):
        """Un administrateur accède à la page."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(reverse("monitoring"))
        self.assertEqual(response.status_code, 200)

    def test_monitoring_uses_correct_template(self):
        """Vérifie le template de la page monitoring."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(reverse("monitoring"))
        self.assertTemplateUsed(response, "www/monitoring.html")


class AdminServicesAccessTest(TestCase):
    """Tests d'accès à la gestion des machines, serveurs et catégories."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.admin = User.objects.create_user(username="adminuser", password="adminpass")
        self.admin.userprofile.user_level = ADMINISTRATEUR
        self.admin.userprofile.save()
        self.categorie = ServiceCategorie.objects.create(
            nom="Infrastructure", slug="infrastructure")
        self.client = Client()

    def test_admin_services_anonymous_redirects(self):
        """Un anonyme est redirigé vers le login."""
        response = self.client.get(reverse("admin_services"))
        self.assertEqual(response.status_code, 302)

    def test_admin_services_regular_user_forbidden(self):
        """Un utilisateur normal reçoit un 403."""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("admin_services"))
        self.assertEqual(response.status_code, 403)

    def test_admin_services_admin_returns_200(self):
        """Un administrateur accède à la page."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(reverse("admin_services"))
        self.assertEqual(response.status_code, 200)

    def test_admin_machine_ajouter_post(self):
        """POST crée une machine."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_machine_ajouter"), {
            "nom": "nas.home.lan",
            "categorie": self.categorie.pk,
            "ports_supplementaires": "",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Machine.objects.filter(nom="nas.home.lan").exists())

    def test_admin_machine_supprimer_post(self):
        """POST supprime une machine."""
        machine = Machine.objects.create(
            nom="Temp", categorie=self.categorie)
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_machine_supprimer", args=[machine.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Machine.objects.filter(pk=machine.pk).exists())

    def test_admin_serveur_ajouter_post(self):
        """POST crée un serveur."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_serveur_ajouter"), {
            "titre": "Grafana",
            "categorie": self.categorie.pk,
            "url": "https://grafana.example.com",
            "adresse": "",
            "port": "",
            "mdi_icon_name": "",
            "icone_url": "",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Serveur.objects.filter(titre="Grafana").exists())

    def test_admin_serveur_supprimer_post(self):
        """POST supprime un serveur."""
        serveur = Serveur.objects.create(
            titre="Temp", categorie=self.categorie,
            url="https://temp.example.com")
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_serveur_supprimer", args=[serveur.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Serveur.objects.filter(pk=serveur.pk).exists())

    def test_admin_service_categorie_ajouter_post(self):
        """POST crée une catégorie de service avec auto-slug."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_service_categorie_ajouter"), {
            "nom": "Monitoring",
            "mdi_icon_name": "",
            "ordre": 1,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ServiceCategorie.objects.filter(slug="monitoring").exists())

    def test_admin_service_categorie_modifier_post(self):
        """POST modifie le nom d'une catégorie."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(
            reverse("admin_service_categorie_modifier", args=[self.categorie.pk]), {
                "nom": "Infra modifiée",
                "mdi_icon_name": "",
                "ordre": 1,
            })
        self.assertEqual(response.status_code, 302)
        self.categorie.refresh_from_db()
        self.assertEqual(self.categorie.nom, "Infra modifiée")

    def test_admin_service_categorie_supprimer_post(self):
        """POST supprime une catégorie."""
        cat = ServiceCategorie.objects.create(nom="Temp", slug="temp-svc")
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.post(reverse("admin_service_categorie_supprimer", args=[cat.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ServiceCategorie.objects.filter(pk=cat.pk).exists())


class MachineModelTest(TestCase):
    """Tests du modèle Machine."""

    def setUp(self):
        self.categorie = ServiceCategorie.objects.create(
            nom="Test", slug="test")

    def test_machine_str_avec_ip(self):
        """Vérifie le __str__ de Machine avec IP résolue."""
        machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie,
            adresse_ip="10.10.0.1")
        self.assertEqual(str(machine), "NAS (10.10.0.1)")

    def test_machine_str_sans_ip(self):
        """Vérifie le __str__ de Machine sans IP résolue."""
        machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie)
        self.assertEqual(str(machine), "NAS")

    def test_machine_ip_statique_valide(self):
        """Vérifie qu'une IP statique dans 10.10.0.0/16 est acceptée."""
        machine = Machine(
            nom="valide.home.lan", categorie=self.categorie,
            ip_statique="10.10.5.42")
        machine.full_clean()  # ne doit pas lever d'erreur

    def test_machine_ip_statique_hors_reseau(self):
        """Vérifie qu'une IP statique hors 10.10.0.0/16 est rejetée."""
        machine = Machine(
            nom="invalide.home.lan", categorie=self.categorie,
            ip_statique="192.168.1.1")
        with self.assertRaises(ValidationError):
            machine.full_clean()

    def test_machine_ip_statique_reseau_10_mais_hors_10_10(self):
        """Vérifie qu'une IP statique en 10.20.x.x est rejetée."""
        machine = Machine(
            nom="invalide.home.lan", categorie=self.categorie,
            ip_statique="10.20.0.1")
        with self.assertRaises(ValidationError):
            machine.full_clean()

    def test_machine_sans_ip_statique_valide(self):
        """Vérifie qu'une machine sans IP statique est acceptée."""
        machine = Machine(
            nom="dhcp.home.lan", categorie=self.categorie)
        machine.full_clean()  # ne doit pas lever d'erreur


class ServeurModelTest(TestCase):
    """Tests du modèle Serveur."""

    def setUp(self):
        self.categorie = ServiceCategorie.objects.create(
            nom="Test", slug="test")

    def _make_serveur(self, **kwargs):
        """Crée un serveur avec les paramètres donnés."""
        defaults = {
            "titre": "Serveur Test",
            "categorie": self.categorie,
            "url": "https://example.com",
        }
        defaults.update(kwargs)
        return Serveur.objects.create(**defaults)

    def test_serveur_icone_html_mdi(self):
        """Vérifie le HTML d'une icône MDI."""
        serveur = self._make_serveur(mdi_icon_name="chart-line")
        html = serveur.icone_html()
        self.assertIn("mdi-chart-line", html)
        self.assertIn("<span", html)

    def test_serveur_icone_html_url(self):
        """Vérifie le HTML d'une icône URL."""
        serveur = self._make_serveur(icone_url="https://example.com/icon.png")
        html = serveur.icone_html()
        self.assertIn("<img", html)
        self.assertIn("https://example.com/icon.png", html)
        self.assertIn("service-icone-img", html)

    def test_serveur_icone_html_vide(self):
        """Vérifie le retour vide sans icône."""
        serveur = self._make_serveur()
        self.assertEqual(serveur.icone_html(), "")

    def test_serveur_has_icone(self):
        """Vérifie le booléen has_icone."""
        serveur_vide = self._make_serveur(titre="Vide")
        self.assertFalse(serveur_vide.has_icone())
        serveur_mdi = self._make_serveur(titre="MDI", mdi_icon_name="star")
        self.assertTrue(serveur_mdi.has_icone())
        serveur_url = self._make_serveur(
            titre="URL", icone_url="https://example.com/i.png")
        self.assertTrue(serveur_url.has_icone())

    def test_serveur_lien_url(self):
        """Vérifie que lien() retourne l'URL."""
        serveur = self._make_serveur(url="https://grafana.local")
        self.assertEqual(serveur.lien(), "https://grafana.local")

    def test_serveur_lien_ip_port(self):
        """Vérifie que lien() retourne ip:port quand pas d'URL."""
        serveur = self._make_serveur(url="", adresse="10.10.0.1", port=8080)
        self.assertEqual(serveur.lien(), "http://10.10.0.1:8080")

    def test_serveur_lien_vide(self):
        """Vérifie que lien() retourne vide sans url ni ip+port."""
        serveur = Serveur(titre="Test", categorie=self.categorie)
        self.assertEqual(serveur.lien(), "")

    def test_serveur_clean_ni_url_ni_adresse(self):
        """Vérifie que clean() rejette sans url ni adresse+port."""
        from django.core.exceptions import ValidationError
        serveur = Serveur(titre="Test", categorie=self.categorie)
        with self.assertRaises(ValidationError):
            serveur.full_clean()

    def test_serveur_reverse_proxy_default_false(self):
        """Vérifie que reverse_proxy_ok est False par défaut."""
        serveur = self._make_serveur()
        self.assertFalse(serveur.reverse_proxy_ok)

    def test_serveur_validation_multiple_modes_icone(self):
        """Vérifie que MDI + URL simultanés génèrent une erreur via le formulaire."""
        admin = User.objects.create_user(username="adminuser3", password="adminpass")
        admin.userprofile.user_level = ADMINISTRATEUR
        admin.userprofile.save()
        self.client.login(username="adminuser3", password="adminpass")
        response = self.client.post(reverse("admin_serveur_ajouter"), {
            "titre": "Serveur Double",
            "categorie": self.categorie.pk,
            "url": "https://example.com",
            "adresse": "",
            "port": "",
            "mdi_icon_name": "star",
            "icone_url": "https://example.com/icon.png",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Serveur.objects.filter(titre="Serveur Double").exists())


import sys

# Mock nmap si non disponible (installé uniquement dans Docker)
if "nmap" not in sys.modules:
    sys.modules["nmap"] = unittest.mock.MagicMock()


class CeleryTasksTest(TestCase):
    """Tests des tâches Celery de vérification."""

    def setUp(self):
        self.categorie = ServiceCategorie.objects.create(
            nom="Infra", slug="infra")

    @unittest.mock.patch("www.tasks._ping", return_value=True)
    @unittest.mock.patch("www.tasks._resoudre_et_mettre_a_jour", return_value=("10.10.0.1", ""))
    def test_verifier_machines_en_ligne(self, mock_resoudre, mock_ping):
        """Vérifie qu'une machine en ligne est mise à jour correctement."""
        machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie)

        from www.tasks import verifier_machines
        verifier_machines()
        machine.refresh_from_db()
        self.assertTrue(machine.en_ligne)
        self.assertIsNotNone(machine.derniere_verification)
        self.assertIsNotNone(machine.derniere_vue_en_ligne)

    @unittest.mock.patch("www.tasks._ping", return_value=False)
    @unittest.mock.patch("www.tasks._resoudre_et_mettre_a_jour", return_value=("10.10.0.2", ""))
    def test_verifier_machines_hors_ligne(self, mock_resoudre, mock_ping):
        """Vérifie qu'une machine hors ligne est mise à jour correctement."""
        machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie)

        from www.tasks import verifier_machines
        verifier_machines()
        machine.refresh_from_db()
        self.assertFalse(machine.en_ligne)
        self.assertIsNotNone(machine.derniere_verification)

    @unittest.mock.patch("www.tasks._verifier_tcp")
    @unittest.mock.patch("www.tasks._verifier_url")
    def test_verifier_serveurs_en_ligne(self, mock_url, mock_tcp):
        """Vérifie qu'un serveur en ligne est mis à jour."""
        serveur = Serveur.objects.create(
            titre="Grafana", categorie=self.categorie,
            url="https://grafana.local")
        mock_url.return_value = True
        mock_tcp.return_value = False

        from www.tasks import verifier_serveurs
        verifier_serveurs()
        serveur.refresh_from_db()
        self.assertTrue(serveur.en_ligne)
        self.assertIsNotNone(serveur.derniere_verification)
        self.assertIsNotNone(serveur.derniere_vue_en_ligne)

    @unittest.mock.patch("www.tasks._verifier_tcp")
    @unittest.mock.patch("www.tasks._verifier_url")
    def test_verifier_serveurs_hors_ligne(self, mock_url, mock_tcp):
        """Vérifie qu'un serveur hors ligne est mis à jour."""
        serveur = Serveur.objects.create(
            titre="Down", categorie=self.categorie,
            url="https://down.local")
        mock_url.return_value = False
        mock_tcp.return_value = False

        from www.tasks import verifier_serveurs
        verifier_serveurs()
        serveur.refresh_from_db()
        self.assertFalse(serveur.en_ligne)

    @unittest.mock.patch("www.tasks._verifier_tcp")
    @unittest.mock.patch("www.tasks._verifier_url")
    def test_verifier_serveurs_reverse_proxy(self, mock_url, mock_tcp):
        """Vérifie le statut reverse proxy quand url + adresse+port."""
        serveur = Serveur.objects.create(
            titre="RP", categorie=self.categorie,
            url="https://rp.local", adresse="10.10.0.5", port=8080)
        mock_url.return_value = True
        mock_tcp.return_value = True

        from www.tasks import verifier_serveurs
        verifier_serveurs()
        serveur.refresh_from_db()
        self.assertTrue(serveur.en_ligne)
        self.assertTrue(serveur.reverse_proxy_ok)


class MachineDetailAccessTest(TestCase):
    """Tests d'accès à la page de détail machine et à l'endpoint SSE."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.admin = User.objects.create_user(username="adminuser", password="adminpass")
        self.admin.userprofile.user_level = ADMINISTRATEUR
        self.admin.userprofile.save()
        self.categorie = ServiceCategorie.objects.create(
            nom="Infra", slug="infra")
        self.machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie)
        self.client = Client()

    def test_detail_anonymous_redirects(self):
        """Un anonyme est redirigé vers le login."""
        response = self.client.get(
            reverse("monitoring_machine_detail", args=[self.machine.pk]))
        self.assertEqual(response.status_code, 302)

    def test_detail_regular_user_forbidden(self):
        """Un utilisateur normal reçoit un 403."""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("monitoring_machine_detail", args=[self.machine.pk]))
        self.assertEqual(response.status_code, 403)

    def test_detail_admin_returns_200(self):
        """Un administrateur accède à la page de détail."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(
            reverse("monitoring_machine_detail", args=[self.machine.pk]))
        self.assertEqual(response.status_code, 200)

    def test_detail_uses_correct_template(self):
        """Vérifie le template de la page détail machine."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(
            reverse("monitoring_machine_detail", args=[self.machine.pk]))
        self.assertTemplateUsed(response, "www/machine_detail.html")

    def test_detail_machine_inexistante_returns_404(self):
        """Une machine inexistante retourne 404."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(
            reverse("monitoring_machine_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

    @unittest.mock.patch("www.tasks.scanner_ping")
    def test_ping_sse_anonymous_redirects(self, mock_scanner):
        """Un anonyme est redirigé vers le login pour l'endpoint SSE ping."""
        response = self.client.get(
            reverse("machine_ping_sse", args=[self.machine.pk]))
        self.assertEqual(response.status_code, 302)

    @unittest.mock.patch("www.tasks.scanner_ping")
    def test_ping_sse_regular_user_forbidden(self, mock_scanner):
        """Un utilisateur normal reçoit un 403 pour l'endpoint SSE ping."""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("machine_ping_sse", args=[self.machine.pk]))
        self.assertEqual(response.status_code, 403)

    @unittest.mock.patch("www.tasks.scanner_ping")
    def test_ping_sse_admin_returns_event_stream(self, mock_scanner):
        """Un administrateur reçoit un content-type text/event-stream pour le ping."""
        mock_scanner.return_value = iter([])
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(
            reverse("machine_ping_sse", args=[self.machine.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response["Content-Type"])

    @unittest.mock.patch("www.tasks.scanner_ports")
    def test_ports_sse_admin_returns_event_stream(self, mock_scanner):
        """Un administrateur reçoit un content-type text/event-stream pour les ports."""
        mock_scanner.return_value = iter([])
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(
            reverse("machine_ports_sse", args=[self.machine.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response["Content-Type"])


class ScannerPingTest(TestCase):
    """Tests du générateur SSE scanner_ping."""

    def setUp(self):
        self.categorie = ServiceCategorie.objects.create(
            nom="Infra", slug="infra")

    @unittest.mock.patch("www.tasks._ping", return_value=True)
    @unittest.mock.patch("www.tasks._resoudre_et_mettre_a_jour", return_value=("10.10.0.1", ""))
    def test_ping_en_ligne(self, mock_resoudre, mock_ping):
        """Vérifie le ping d'une machine en ligne."""
        machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie)

        from www.tasks import scanner_ping
        events = list(scanner_ping(machine.pk))
        self.assertEqual(len(events), 2)
        self.assertIn("event: ping", events[0])
        self.assertIn('"en_ligne": true', events[0])
        self.assertIn('"adresse_ip": "10.10.0.1"', events[0])
        self.assertIn("event: done", events[1])

        machine.refresh_from_db()
        self.assertTrue(machine.en_ligne)
        self.assertIsNotNone(machine.derniere_vue_en_ligne)

    @unittest.mock.patch("www.tasks._ping", return_value=False)
    @unittest.mock.patch("www.tasks._resoudre_et_mettre_a_jour", return_value=("10.10.0.2", ""))
    def test_ping_hors_ligne(self, mock_resoudre, mock_ping):
        """Vérifie le ping d'une machine hors ligne."""
        machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie)

        from www.tasks import scanner_ping
        events = list(scanner_ping(machine.pk))
        self.assertEqual(len(events), 2)
        self.assertIn("event: ping", events[0])
        self.assertIn('"en_ligne": false', events[0])

        machine.refresh_from_db()
        self.assertFalse(machine.en_ligne)


class ScannerPortsTest(TestCase):
    """Tests du générateur SSE scanner_ports (scan par morceaux)."""

    def setUp(self):
        self.categorie = ServiceCategorie.objects.create(
            nom="Infra", slug="infra")

    @unittest.mock.patch("nmap.PortScanner")
    @unittest.mock.patch("www.tasks._resoudre_et_mettre_a_jour", return_value=("10.10.0.1", ""))
    def test_scan_ports(self, mock_resoudre, mock_scanner_cls):
        """Vérifie le scan des ports par morceaux."""
        machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie)

        mock_nm = unittest.mock.MagicMock()
        mock_nm.all_hosts.return_value = ["10.10.0.1"]
        host_result = unittest.mock.MagicMock()
        host_result.all_protocols.return_value = ["tcp"]
        host_result.__getitem__ = unittest.mock.MagicMock(return_value={
            22: {"state": "open", "name": "ssh", "version": "8.0"},
            80: {"state": "closed", "name": "http", "version": ""},
        })
        mock_nm.__getitem__ = unittest.mock.MagicMock(return_value=host_result)
        mock_nm.__contains__ = unittest.mock.MagicMock(return_value=True)
        mock_scanner_cls.return_value = mock_nm

        from www.tasks import scanner_ports, _expand_ports, PORTS_COURANTS, TAILLE_CHUNK_PORTS
        events = list(scanner_ports(machine.pk))

        # N événements ports (un par chunk) + 1 done
        nb_ports = len(set(_expand_ports(PORTS_COURANTS)))
        nb_chunks = (nb_ports + TAILLE_CHUNK_PORTS - 1) // TAILLE_CHUNK_PORTS
        self.assertEqual(len(events), nb_chunks + 1)
        # Tous les événements sauf le dernier sont des ports
        for event in events[:-1]:
            self.assertIn("event: ports", event)
        self.assertIn("event: done", events[-1])

        machine.refresh_from_db()
        self.assertIsNotNone(machine.dernier_scan_ports)

    @unittest.mock.patch("nmap.PortScanner")
    @unittest.mock.patch("www.tasks._resoudre_et_mettre_a_jour", return_value=(None, "DNS impossible"))
    def test_scan_ports_sans_ip(self, mock_resoudre, mock_scanner_cls):
        """Vérifie le scan des ports quand l'IP est None."""
        machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie)

        from www.tasks import scanner_ports
        events = list(scanner_ports(machine.pk))
        self.assertEqual(len(events), 2)
        self.assertIn("event: ports", events[0])
        self.assertIn("event: done", events[1])

        machine.refresh_from_db()
        self.assertEqual(machine.ports_ouverts, [])



class ServeurDetailAccessTest(TestCase):
    """Tests d'accès à la page de détail serveur et à l'endpoint SSE."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.admin = User.objects.create_user(username="adminuser", password="adminpass")
        self.admin.userprofile.user_level = ADMINISTRATEUR
        self.admin.userprofile.save()
        self.categorie = ServiceCategorie.objects.create(
            nom="Infra", slug="infra")
        self.serveur = Serveur.objects.create(
            titre="Grafana", categorie=self.categorie,
            url="https://grafana.local")
        self.client = Client()

    def test_detail_anonymous_redirects(self):
        """Un anonyme est redirigé vers le login."""
        response = self.client.get(
            reverse("monitoring_serveur_detail", args=[self.serveur.pk]))
        self.assertEqual(response.status_code, 302)

    def test_detail_regular_user_forbidden(self):
        """Un utilisateur normal reçoit un 403."""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("monitoring_serveur_detail", args=[self.serveur.pk]))
        self.assertEqual(response.status_code, 403)

    def test_detail_admin_returns_200(self):
        """Un administrateur accède à la page de détail."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(
            reverse("monitoring_serveur_detail", args=[self.serveur.pk]))
        self.assertEqual(response.status_code, 200)

    def test_detail_uses_correct_template(self):
        """Vérifie le template de la page détail serveur."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(
            reverse("monitoring_serveur_detail", args=[self.serveur.pk]))
        self.assertTemplateUsed(response, "www/serveur_detail.html")

    def test_detail_serveur_inexistant_returns_404(self):
        """Un serveur inexistant retourne 404."""
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(
            reverse("monitoring_serveur_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

    @unittest.mock.patch("www.tasks.scanner_serveur")
    def test_check_sse_admin_returns_event_stream(self, mock_scanner):
        """Un administrateur reçoit un content-type text/event-stream."""
        mock_scanner.return_value = iter([])
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(
            reverse("serveur_check_sse", args=[self.serveur.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response["Content-Type"])

    def test_detail_affiche_description(self):
        """Vérifie que la description est visible sur la page de détail."""
        self.serveur.description = "Tableau de bord"
        self.serveur.save()
        self.client.login(username="adminuser", password="adminpass")
        response = self.client.get(
            reverse("monitoring_serveur_detail", args=[self.serveur.pk]))
        self.assertContains(response, "Tableau de bord")


class ServeurHostnameTest(TestCase):
    """Tests du support hostname pour les serveurs."""

    def setUp(self):
        self.categorie = ServiceCategorie.objects.create(
            nom="Infra", slug="infra")

    def test_serveur_avec_hostname(self):
        """Un serveur peut être créé avec un hostname au lieu d'une IP."""
        serveur = Serveur(
            titre="DNS", categorie=self.categorie,
            hostname="dns.local", port=53)
        serveur.full_clean()
        serveur.save()
        self.assertEqual(serveur.adresse_effective(), "dns.local")

    def test_serveur_adresse_effective_ip_prioritaire(self):
        """L'adresse IP est prioritaire sur le hostname."""
        serveur = Serveur(
            titre="Test", categorie=self.categorie,
            adresse="10.10.0.1", hostname="test.local", port=80)
        self.assertEqual(serveur.adresse_effective(), "10.10.0.1")

    def test_serveur_lien_avec_hostname(self):
        """Le lien utilise le hostname quand pas d'IP."""
        serveur = Serveur(
            titre="App", categorie=self.categorie,
            hostname="app.local", port=8080)
        self.assertEqual(serveur.lien(), "http://app.local:8080")

    def test_serveur_validation_sans_adresse_ni_url(self):
        """La validation échoue sans URL ni adresse/hostname + port."""
        serveur = Serveur(titre="Vide", categorie=self.categorie)
        with self.assertRaises(ValidationError):
            serveur.full_clean()

    def test_serveur_formulaire_hostname(self):
        """Le formulaire accepte un hostname."""
        admin = User.objects.create_user(username="adminuser", password="adminpass")
        admin.userprofile.user_level = ADMINISTRATEUR
        admin.userprofile.save()
        client = Client()
        client.login(username="adminuser", password="adminpass")
        response = client.post(reverse("admin_serveur_ajouter"), {
            "titre": "DNS",
            "categorie": self.categorie.pk,
            "description": "Serveur DNS local",
            "url": "",
            "hostname": "dns.local",
            "adresse": "",
            "port": 53,
            "mdi_icon_name": "",
            "icone_image": "",
            "icone_url": "",
        })
        self.assertEqual(response.status_code, 302)
        serveur = Serveur.objects.get(titre="DNS")
        self.assertEqual(serveur.hostname, "dns.local")
        self.assertEqual(serveur.description, "Serveur DNS local")


class ScannerServeurTest(TestCase):
    """Tests du générateur SSE scanner_serveur."""

    def setUp(self):
        self.categorie = ServiceCategorie.objects.create(
            nom="Infra", slug="infra")

    @unittest.mock.patch("www.tasks._verifier_tcp", return_value=True)
    @unittest.mock.patch("www.tasks._verifier_url", return_value=True)
    def test_scanner_serveur_en_ligne(self, mock_url, mock_tcp):
        """Vérifie le scan d'un serveur en ligne."""
        serveur = Serveur.objects.create(
            titre="Grafana", categorie=self.categorie,
            url="https://grafana.local")

        from www.tasks import scanner_serveur
        events = list(scanner_serveur(serveur.pk))
        self.assertEqual(len(events), 2)
        self.assertIn("event: check", events[0])
        self.assertIn('"en_ligne": true', events[0])
        self.assertIn("event: done", events[1])

        serveur.refresh_from_db()
        self.assertTrue(serveur.en_ligne)
        self.assertIsNotNone(serveur.derniere_verification)

    @unittest.mock.patch("www.tasks._verifier_tcp", return_value=False)
    @unittest.mock.patch("www.tasks._verifier_url", return_value=False)
    def test_scanner_serveur_hors_ligne(self, mock_url, mock_tcp):
        """Vérifie le scan d'un serveur hors ligne."""
        serveur = Serveur.objects.create(
            titre="Down", categorie=self.categorie,
            url="https://down.local")

        from www.tasks import scanner_serveur
        events = list(scanner_serveur(serveur.pk))
        self.assertEqual(len(events), 2)
        self.assertIn('"en_ligne": false', events[0])

        serveur.refresh_from_db()
        self.assertFalse(serveur.en_ligne)

    @unittest.mock.patch("www.tasks._verifier_tcp", return_value=True)
    @unittest.mock.patch("www.tasks._verifier_url", return_value=False)
    def test_scanner_serveur_hostname(self, mock_url, mock_tcp):
        """Vérifie le scan avec hostname au lieu d'IP."""
        serveur = Serveur.objects.create(
            titre="App", categorie=self.categorie,
            hostname="app.local", port=8080)

        from www.tasks import scanner_serveur
        events = list(scanner_serveur(serveur.pk))
        serveur.refresh_from_db()
        self.assertTrue(serveur.en_ligne)
        mock_tcp.assert_called_with("app.local", 8080)


class MachineHostnameTest(TestCase):
    """Tests du hostname et de la résolution DNS des machines."""

    def setUp(self):
        self.categorie = ServiceCategorie.objects.create(
            nom="Infra", slug="infra")

    def test_hostname_complet_avec_point(self):
        """Un nom avec un point est retourné tel quel."""
        machine = Machine(
            nom="nas.home.lan", categorie=self.categorie)
        self.assertEqual(machine.hostname_complet(), "nas.home.lan")

    def test_hostname_complet_sans_point_avec_domaine(self):
        """Un nom court est complété par le domaine par défaut."""
        with self.settings(MONITORING_DOMAINE_DEFAUT="home.lan"):
            machine = Machine(
                nom="nas", categorie=self.categorie)
            self.assertEqual(machine.hostname_complet(), "nas.home.lan")

    def test_hostname_complet_sans_point_sans_domaine(self):
        """Un nom court sans domaine par défaut est retourné tel quel."""
        with self.settings(MONITORING_DOMAINE_DEFAUT=""):
            machine = Machine(
                nom="nas", categorie=self.categorie)
            self.assertEqual(machine.hostname_complet(), "nas")

    @unittest.mock.patch("socket.gethostbyname", return_value="10.10.0.42")
    def test_resoudre_ip_succes(self, mock_dns):
        """Résolution DNS réussie retourne l'IP."""
        machine = Machine(
            nom="NAS", categorie=self.categorie)
        ip, alerte = machine.resoudre_ip()
        self.assertEqual(ip, "10.10.0.42")
        self.assertEqual(alerte, "")

    @unittest.mock.patch("socket.gethostbyname", side_effect=socket.gaierror)
    def test_resoudre_ip_echec_dns(self, mock_dns):
        """Échec DNS retourne None et un message d'alerte."""
        machine = Machine(
            nom="inconnu.home.lan", categorie=self.categorie)
        ip, alerte = machine.resoudre_ip()
        self.assertIsNone(ip)
        self.assertIn("Résolution DNS impossible", alerte)

    @unittest.mock.patch("socket.gethostbyname", return_value="192.168.1.1")
    def test_resoudre_ip_hors_reseau(self, mock_dns):
        """IP résolue hors réseau local retourne une alerte."""
        machine = Machine(
            nom="NAS", categorie=self.categorie)
        ip, alerte = machine.resoudre_ip()
        self.assertEqual(ip, "192.168.1.1")
        self.assertIn("hors du réseau", alerte)

    @unittest.mock.patch("socket.gethostbyname", return_value="10.10.0.42")
    def test_resoudre_ip_divergence_ip_statique(self, mock_dns):
        """IP résolue différente de l'IP statique génère une alerte."""
        machine = Machine(
            nom="NAS", categorie=self.categorie,
            ip_statique="10.10.0.99")
        ip, alerte = machine.resoudre_ip()
        self.assertEqual(ip, "10.10.0.42")
        self.assertIn("différente", alerte)

    @unittest.mock.patch("socket.gethostbyname", return_value="10.10.0.42")
    def test_resoudre_ip_coherente_ip_statique(self, mock_dns):
        """IP résolue cohérente avec l'IP statique ne génère pas d'alerte."""
        machine = Machine(
            nom="NAS", categorie=self.categorie,
            ip_statique="10.10.0.42")
        ip, alerte = machine.resoudre_ip()
        self.assertEqual(ip, "10.10.0.42")
        self.assertEqual(alerte, "")


class MachineResolutionDnsTest(TestCase):
    """Tests de la résolution DNS dans les tâches scanner."""

    def setUp(self):
        self.categorie = ServiceCategorie.objects.create(
            nom="Infra", slug="infra")

    @unittest.mock.patch("www.tasks._ping", return_value=True)
    @unittest.mock.patch("www.tasks._resoudre_et_mettre_a_jour", return_value=("10.10.0.42", ""))
    def test_scanner_ping_resout_ip(self, mock_resoudre, mock_ping):
        """scanner_ping résout l'IP et la retourne dans l'événement SSE."""
        machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie)

        from www.tasks import scanner_ping
        events = list(scanner_ping(machine.pk))
        self.assertIn('"adresse_ip": "10.10.0.42"', events[0])
        self.assertIn('"alerte_ip": ""', events[0])

    @unittest.mock.patch("www.tasks._ping", return_value=False)
    @unittest.mock.patch("www.tasks._resoudre_et_mettre_a_jour", return_value=(None, "Résolution DNS impossible pour nas.home.lan"))
    def test_scanner_ping_dns_echoue(self, mock_resoudre, mock_ping):
        """scanner_ping quand DNS échoue → machine hors ligne + alerte."""
        machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie)

        from www.tasks import scanner_ping
        events = list(scanner_ping(machine.pk))
        self.assertIn('"en_ligne": false', events[0])
        self.assertIn("Résolution DNS impossible", events[0])
        # _ping ne doit pas être appelé si IP est None
        mock_ping.assert_not_called()

    @unittest.mock.patch("www.tasks._ping", return_value=True)
    @unittest.mock.patch("www.tasks._resoudre_et_mettre_a_jour")
    def test_scanner_ping_divergence_alerte(self, mock_resoudre, mock_ping):
        """scanner_ping avec divergence → alerte dans l'événement SSE."""
        alerte = "IP résolue (10.10.0.42) différente de l'IP statique attendue (10.10.0.99)"
        mock_resoudre.return_value = ("10.10.0.42", alerte)

        machine = Machine.objects.create(
            nom="NAS", categorie=self.categorie,
            ip_statique="10.10.0.99")

        from www.tasks import scanner_ping
        events = list(scanner_ping(machine.pk))
        self.assertIn('"en_ligne": true', events[0])
        self.assertIn("différente", events[0])
