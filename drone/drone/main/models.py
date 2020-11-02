"""main.models"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify


# Page des articles: les articles et leur commentaires
class Article(models.Model):
    """
    object to manipulate articles
    """
    titre = models.CharField(max_length=100, verbose_name="Titre de l'article")
    slug = models.SlugField(max_length=100, verbose_name="slug de l'article")
    # auteur = models.CharField(max_length=42, verbose_name="Auteur de l'article")
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Auteur de l'article")
    contenu = MarkdownxField(blank=True, default="", verbose_name="Contenu de l'article au format Markdown")
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de parution")

    def contenu_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return markdownify(str(self.contenu))

    def nb_comments(self):
        return len(self.get_comments())

    def get_comments(self):
        return self.comments.filter(active=True)

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "article"
        ordering = ['date']

    def __str__(self):
        return self.titre


class ArticleComments(models.Model):
    """
    base class for storing comments
    """
    article = models.ForeignKey(Article,
                                on_delete=models.CASCADE,
                                verbose_name="Article du commentaire",
                                related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete=models.CASCADE, verbose_name="Auteur du commentaire")
    contenu = MarkdownxField(blank=True, default="", verbose_name="Contenu de l'article au format Markdown")
    date = models.DateTimeField(default=timezone.now, verbose_name="Date de parution")
    active = models.BooleanField(default=False)

    def contenu_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return markdownify(str(self.contenu))

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "Commentaire d'article"
        ordering = ['date']

    def __str__(self):
        return str(self.user) + "_" + str(self.date)


# page de composants: les composant et leur catégorie
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
    specs = models.JSONField(blank=True, default=dict, verbose_name="Caractéristiques")
    comments = MarkdownxField(blank=True, default="", verbose_name="Commentaires")
    datasheet = models.URLField(null=True, blank=True, verbose_name="Liens vers la datasheet")
    photo = models.ImageField(null=True, blank=True, verbose_name="Photo du composant")

    def __str__(self):
        return self.name

    def comments_md(self):
        """
        render the comments as Markdown
        :return: the html output
        """
        return markdownify(str(self.comments))


# page de configuration: les configuration et leur commentaires
class DroneConfiguration(models.Model):
    """
    class for describing drone configuration
    """
    version_number = models.CharField(max_length=10, verbose_name="Numéro de version")
    nick_name = models.CharField(max_length=40, blank=True, default="", verbose_name="Surnon de la version")
    date = models.DateTimeField(default=timezone.now, verbose_name="Date de realisation")
    Composants = models.ManyToManyField(DroneComponent)
    version_logiciel = models.CharField(max_length=40, blank=True, default="",
                                        verbose_name="Version du logiciel du contrôleur de vol")
    description = MarkdownxField(blank=True, default="", verbose_name="Commentaires")
    photo = models.ImageField(null=True, blank=True, verbose_name="Photo de la configuration")

    class Meta:
        """
        Meta data for drone
        """
        verbose_name = "Configuration Drone"
        ordering = ['date']

    def description_md(self):
        """
        render the description as Markdown
        :return: the html output
        """
        return markdownify(str(self.description))

    def __str__(self):
        if self.nick_name not in [None, ""]:
            return "Version " + str(self.version_number) + " " + str(self.nick_name)
        return "Version " + str(self.version_number)

    def nb_comments(self):
        return len(self.get_comments())

    def get_comments(self):
        return self.comments.filter(active=True)


class ConfigurationComments(models.Model):
    """
    base class for storing comments
    """
    article = models.ForeignKey(DroneConfiguration,
                                on_delete=models.CASCADE,
                                verbose_name="Article du commentaire",
                                related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete=models.CASCADE, verbose_name="Auteur du commentaire")
    contenu = MarkdownxField(blank=True, default="", verbose_name="Contenu de l'article au format Markdown")
    date = models.DateTimeField(default=timezone.now, verbose_name="Date de parution")
    active = models.BooleanField(default=False)

    def contenu_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return markdownify(str(self.contenu))

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "Commentaire d'article"
        ordering = ['date']

    def __str__(self):
        return str(self.user) + "_" + str(self.date)


# page des vols: les vols (encore en et leur commentaires
class DroneFlight(models.Model):
    """
    class handling drone flights
    TODO: refactor de cette classe
    """
    date = models.DateTimeField(default=timezone.now, verbose_name="Date de realisation")
    name = models.CharField(max_length=40, blank=True, default="")
    # TODO: gestion de la météo avec affichage des icones
    meteo = models.JSONField(blank=True, default=dict)
    drone_configuration = models.ForeignKey('DroneConfiguration', on_delete=models.CASCADE)
    summary = MarkdownxField()

    class Meta:
        """
        Meta data for drone
        """
        verbose_name = "Vol de  Drone"
        ordering = ['-date']

    def summary_md(self):
        """
        render the summary as Markdown
        :return: the html output
        """
        return markdownify(str(self.summary))

    def nb_comments(self):
        return len(self.get_comments())

    def get_comments(self):
        return self.comments.filter(active=True)

    def __str__(self):
        if self.name not in [None, ""]:
            return str(self.name) + " du " + str(self.date)
        return "Vol du " + str(self.date)


class FlightComments(models.Model):
    """
    base class for storing comments
    """
    article = models.ForeignKey(DroneFlight,
                                on_delete=models.CASCADE,
                                verbose_name="Article du commentaire",
                                related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete=models.CASCADE, verbose_name="Auteur du commentaire")
    contenu = MarkdownxField(blank=True, default="", verbose_name="Contenu de l'article au format Markdown")
    date = models.DateTimeField(default=timezone.now, verbose_name="Date de parution")
    active = models.BooleanField(default=False)

    def contenu_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return markdownify(str(self.contenu))

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "Commentaire d'article"
        ordering = ['date']

    def __str__(self):
        return str(self.user) + "_" + str(self.date)

