"""model.py exemple de profile user"""
from django.db import models
from common.models import SiteArticle, SiteArticleComment


class Category(models.Model):
    """
    Category for articles
    """
    nom = models.CharField(max_length=30)
    mdi_icon_name = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.nom


class SubCategory(models.Model):
    """
    Sub Category for articles
    """
    nom = models.CharField(max_length=30)
    mdi_icon_name = models.CharField(max_length=30, blank=True)
    # image = models.ImageField(upload_to="SousCateIcons/",blank=True)

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
        verbose_name = "Commentaire d'article"
        ordering = ['-date']
