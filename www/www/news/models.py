"""news.models"""
from django.db import models
from django.utils import timezone


class Categorie(models.Model):
    """
    Category for articles
    """
    nom = models.CharField(max_length=30)
    mdi_icon_name = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.nom


class SousCategorie(models.Model):
    """
    Sub Category for articles
    """
    nom = models.CharField(max_length=30)
    mdi_icon_name = models.CharField(max_length=30, blank=True)

    # image = models.ImageField(upload_to="SousCateIcons/",blank=True)
    def __str__(self):
        return self.nom


class Article(models.Model):
    """
    object to manipulate articles
    """
    titre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    auteur = models.CharField(max_length=42)
    contenu = models.TextField(null=True)
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de parution")
    categorie = models.ForeignKey('Categorie', on_delete=models.CASCADE)
    sous_categorie = models.ForeignKey('SousCategorie', on_delete=models.CASCADE)
    needuser = models.BooleanField(default=False)
    ishidden = models.BooleanField(default=False)

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "article"
        ordering = ['date']

    def __str__(self):
        return self.titre


class ServerPage(models.Model):
    """
    base class for pages, used for the semi-external pages (page on the same server but other adress)
    """
    name = models.CharField(max_length=30)
    url = models.CharField(max_length=200)
    icon = models.CharField(max_length=40)
    needUser = models.BooleanField()
    needDevAccess = models.BooleanField()
    needHiddenAccess = models.BooleanField()
    isActive = models.BooleanField()


class WebPage(ServerPage):
    """
    class to handle the list of webpages inside this site
    """
    template = models.CharField(max_length=30)
    title = models.CharField(max_length=30)
    categorie = models.ForeignKey('Categorie', on_delete=models.CASCADE)
    data = models.JSONField()


class subWebPage(ServerPage):
    """
    class to handle sub pages in web pages
    """
    parent = models.ForeignKey('WebPage', on_delete=models.CASCADE)
    data = models.JSONField()
