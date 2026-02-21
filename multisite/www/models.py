"""model.py exemple de profile user"""
from django.db import models
from django.utils.html import escape, mark_safe

from markdownx.models import MarkdownxField
from markdownx.utils import markdownify

from common.models import SiteArticle, SiteArticleComment


VISIBILITE_CHOICES = [
    (-1, "Public"),
    (0, "Enregistré"),
    (1, "Autorisé"),
    (2, "Avancé"),
    (3, "Administrateur"),
]


class Category(models.Model):
    """
    Category for articles
    """
    nom = models.CharField(max_length=30)
    mdi_icon_name = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.nom


class SubCategory(models.Model):
    """
    Sub Category for articles
    """
    nom = models.CharField(max_length=30)
    mdi_icon_name = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = "Sous-catégorie"
        verbose_name_plural = "Sous-catégories"

    def __str__(self):
        return self.nom


class Article(SiteArticle):
    """
    Juste une classe basique d'article qui est relié à un `User`
    """
    categorie = models.ForeignKey(
            Category, on_delete=models.CASCADE,
            verbose_name="La catégorie de l'article")
    sous_categorie = models.ForeignKey(
            SubCategory, on_delete=models.CASCADE,
            verbose_name="La sous-catégorie")

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "www article"
        ordering = ['-date']


class ArticleComment(SiteArticleComment):
    """
    Classe pour les commentaires d’article
    """
    class Meta:
        """
        Meta data
        """
        verbose_name = "Commentaire d’article"
        ordering = ['-date']


class ProjetCategorie(models.Model):
    """Catégorie de projet."""
    nom = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    mdi_icon_name = models.CharField(max_length=30, blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        """Meta data"""
        ordering = ["ordre", "nom"]
        verbose_name = "catégorie de projet"
        verbose_name_plural = "catégories de projet"

    def __str__(self):
        return self.nom


class Projet(models.Model):
    """Projet personnel."""
    titre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    categorie = models.ForeignKey(
        ProjetCategorie, on_delete=models.CASCADE,
        related_name="projets", verbose_name="Catégorie")
    resume = models.CharField(max_length=300, verbose_name="Résumé")
    contenu = MarkdownxField(blank=True, verbose_name="Contenu")
    lien_externe = models.URLField(blank=True, verbose_name="Lien externe")
    mdi_icon_name = models.CharField(max_length=30, blank=True)
    icone_image = models.ImageField(blank=True, upload_to="projet_icones", verbose_name="Icône (image)")
    icone_url = models.URLField(blank=True, verbose_name="Icône (URL)")
    couleur = models.CharField(max_length=7, default="#5090C1", verbose_name="Couleur")
    date_creation = models.DateField(verbose_name="Date de création")
    actif = models.BooleanField(default=True)
    visibilite = models.IntegerField(
        default=-1, choices=VISIBILITE_CHOICES,
        verbose_name="Visibilité minimum")
    ordre = models.IntegerField(default=0)

    class Meta:
        """Meta data"""
        ordering = ["ordre", "-date_creation"]
        verbose_name = "projet"
        verbose_name_plural = "projets"

    def __str__(self):
        return self.titre

    def has_icone(self):
        """Vérifie si le projet possède une icône (quel que soit le mode)."""
        return bool(self.mdi_icon_name or self.icone_image or self.icone_url)

    def icone_html(self):
        """Retourne le HTML de l'icône selon le mode actif."""
        if self.icone_image:
            return mark_safe(f'<img src="{escape(self.icone_image.url)}" class="projet-icone-img">')
        if self.icone_url:
            return mark_safe(f'<img src="{escape(self.icone_url)}" class="projet-icone-img">')
        if self.mdi_icon_name:
            return mark_safe(f'<span class="mdi mdi-{escape(self.mdi_icon_name)}"></span>')
        return ""

    def contenu_md(self):
        """Retourne le contenu converti en HTML."""
        return markdownify(self.contenu)
