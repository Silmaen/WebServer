"""main.models"""
from django.db import models
from django.utils import timezone
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify


class Article(models.Model):
    """
    object to manipulate articles
    """
    titre = models.CharField(max_length=100, verbose_name="Titre de l'article")
    slug = models.SlugField(max_length=100, verbose_name="slug de l'article")
    auteur = models.CharField(max_length=42, verbose_name="Auteur de l'article")
    contenu = MarkdownxField(null=True, verbose_name="Contenu de l'article au format Markdown")
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de parution")

    def contenu_md(self):
        return markdownify(self.contenu)

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "article"
        ordering = ['date']

    def __str__(self):
        return self.titre


class DroneComponentCategory(models.Model):
    """
    class to handle component types for drones
    """
    name = models.CharField(max_length=40, verbose_name="Nom de la catégorie")
    onBoard = models.BooleanField(verbose_name="Composant volant ou restant au sol")

    def __str__(self):
        return self.name


class DroneComponent(models.Model):
    """
    class to handle components of drone
    """
    name = models.CharField(max_length=40, verbose_name="Nom du composant")
    category = models.ForeignKey('DroneComponentCategory', on_delete=models.CASCADE, verbose_name="Catégorie")
    specs = models.JSONField(null=True, verbose_name="Caractéristiques")
    comments = MarkdownxField(null=True, verbose_name="Commentaires")
    datasheet = models.URLField(null=True, verbose_name="Liens vers la datasheet")
    photo = models.ImageField(null=True, verbose_name="Photo du composant")

    def __str__(self):
        return self.name

    def comments_md(self):
        return markdownify(self.comments)


# Create your models here.
class DroneConfiguration(models.Model):
    """
    class for describing drone configuration
    """
    version_number = models.CharField(max_length=10, verbose_name="Numéro de version")
    nick_name = models.CharField(max_length=40, null=True, verbose_name="Surnon de la version")
    specs = models.JSONField(null=True, verbose_name="Caractéristiques")
    comments = MarkdownxField(null=True, verbose_name="Commentaires")
    date = models.DateTimeField(default=timezone.now, verbose_name="Date de realisation")
    photo = models.ImageField(null=True, verbose_name="Photo de la configuration")

    class Meta:
        """
        Meta data for drone
        """
        verbose_name = "Configuration Drone"
        ordering = ['date']

    def comments_md(self):
        return markdownify(self.comments)

    def __str__(self):
        if self.nick_name not in [None, ""]:
            return "Version " + str(self.version_number) + " " + str(self.nick_name)
        return "Version " + str(self.version_number)


class DroneFlight(models.Model):
    """
    class handling drone flights
    """
    date = models.DateTimeField(default=timezone.now, verbose_name="Date de realisation")
    name = models.CharField(max_length=40, null=True)
    meteo = models.TextField(null=True)
    summary = MarkdownxField()
    comments = MarkdownxField()
    drone_configuration = models.ForeignKey('DroneConfiguration', on_delete=models.CASCADE)

    class Meta:
        """
        Meta data for drone
        """
        verbose_name = "Vol de  Drone"
        ordering = ['date']

    def comments_md(self):
        return markdownify(self.comments)

    def summary_md(self):
        return markdownify(self.summary)

    def __str__(self):
        if self.name not in [None, ""]:
            return str(self.name) + " du " + str(self.date)
        return "Vol du " + str(self.date)
