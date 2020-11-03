"""main.models"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify
from django.utils.text import Truncator


truncation = 200
comment_truncation = 100


# Page des articles: les articles et leur commentaires
class Article(models.Model):
    """
    object to manipulate articles
    """
    titre = models.CharField(max_length=100, verbose_name="Titre de l'article")
    slug = models.SlugField(max_length=100, verbose_name="slug de l'article")
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Auteur de l'article")
    contenu = MarkdownxField(blank=True, default="", verbose_name="Contenu de l'article au format Markdown")
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de parution")

    def contenu_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return Truncator(markdownify(str(self.contenu))).chars(truncation, truncate='...', html=True)

    def contenu_all_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return markdownify(str(self.contenu))

    def nb_comments(self):
        """
        return the number of comments attached to this object
        :return: number of comments
        """
        return len(self.get_all_comments())

    def get_comments(self):
        """
        return the last 3 comments for this object
        :return: last 3 comments
        """
        return self.get_all_comments()[:3]

    def get_all_comments(self):
        """
        get all comments of this object
        :return: all comments
        """
        return self.comments.filter(active=True).order_by("-date")

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
                                verbose_name="Article lié",
                                related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete=models.CASCADE,
                             verbose_name="Auteur du commentaire")
    contenu = MarkdownxField(blank=True, default="",
                             verbose_name="Contenu du commentaire au format Markdown")
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de parution")
    active = models.BooleanField(default=False)

    def contenu_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return Truncator(markdownify(str(self.contenu))).chars(comment_truncation, truncate='...', html=True)

    def contenu_all_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return markdownify(str(self.contenu))

    def content_overview(self):
        """
        Returns the 40 first characters of the article's content,
        followed by '...' is text is longer.
        """
        return Truncator(self.contenu).chars(comment_truncation, truncate='...')

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "Commentaire d'article"
        ordering = ['-date']

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

    def render_onboard(self):
        """get icon for flying/ ground definition"""
        #                              ground        flying
        return '<span class="mdi ' + ["mdi-download", "mdi-upload"][self.onBoard] + '"></span>'

    def render_name(self):
        stri = '<span class="mdi '
        if self.name == "Hélice":
            stri += 'mdi-fan"></span><span>Hélice</span>'
        elif self.name == "Batterie":
            stri += 'mdi-battery-outline"></span><span>Batterie</span>'
        elif self.name == "Moteur":
            stri += 'mdi-cog-outline"></span><span>Moteur</span>'
        elif self.name == "ESC (contrôleur de puissance moteur)":
            stri += 'mdi-car-cruise-control"></span><span>ESC</span>'
        elif self.name == "Caméra":
            stri += 'mdi-video-outline"></span><span>Caméra</span>'
        elif self.name == "VTX (transmetteur vidéo)":
            stri += 'mdi-video-wireless-outline"></span><span>VTX</span>'
        elif self.name == "Récepteur Vidéo":
            stri += 'mdi-camera-wireless-outline"></span><span>VRX</span>'
        elif self.name == "Télécommande":
            stri += 'mdi-controller-classic-outline"></span><span>Télécommande</span>'
        elif self.name == "Récepteur télémétrie":
            stri += 'mdi-home-thermometer-outline></span><span>Télémétrie sol</span>'
        elif self.name == "Module de radio commande":
            stri += 'mdi-antenna"></span><span>radio commande</span>'
        elif self.name == "Distributeur de puissance":
            stri += 'mdi-power-plug-outline"></span><span>Distributeur de puissance</span>'
        elif self.name == "Module de Télémétrie":
            stri += 'mdi-router-wireless"></span><span>Module Telemétrie</span>'
        elif self.name == "Controleur de vol":
            stri += 'mdi-chip"></span><span>radio commande</span>'
        elif self.name == "Cadre":
            stri += 'mdi-quadcopter"></span><span>radio commande</span>'
        else:
            stri += 'mdi-cogs"></span><span>' + str(self.name) + '</span>'
        return stri

    def render_all(self):
        return self.render_name() + self.render_onboard()


class DroneComponent(models.Model):
    """
    class to handle components of drone
    """
    name = models.CharField(max_length=40,
                            verbose_name="Nom du composant")
    category = models.ForeignKey('DroneComponentCategory', on_delete=models.CASCADE,
                                 verbose_name="Catégorie")
    specs = models.JSONField(blank=True, default=dict,
                             verbose_name="Caractéristiques")
    description = MarkdownxField(blank=True, default="",
                                 verbose_name="Description")
    datasheet = models.URLField(null=True, blank=True,
                                verbose_name="Liens vers la datasheet")
    photo = models.ImageField(null=True, blank=True,
                              upload_to='compimg',
                              verbose_name="Photo du composant")

    def __str__(self):
        return self.name

    def description_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return Truncator(markdownify(str(self.description))).chars(truncation, truncate='...', html=True)

    def description_all_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return markdownify(str(self.description))

    def nb_comments(self):
        """
        return the number of comments attached to this object
        :return: number of comments
        """
        return len(self.get_all_comments())

    def get_comments(self):
        """
        return the last 3 comments for this object
        :return: last 3 comments
        """
        return self.get_all_comments()[:3]

    def get_all_comments(self):
        """
        get all comments of this object
        :return: all comments
        """
        return self.comments.filter(active=True).order_by("-date")


class DroneComponentComments(models.Model):
    """
    base class for storing comments
    """
    article = models.ForeignKey(DroneComponent,
                                on_delete=models.CASCADE,
                                verbose_name="Composant de drone lié",
                                related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete=models.CASCADE,
                             verbose_name="Auteur du commentaire")
    contenu = MarkdownxField(blank=True, default="",
                             verbose_name="Contenu du commentaire au format Markdown")
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de parution")
    active = models.BooleanField(default=False)

    def contenu_md(self):
        """
        render the content as Markdown
        :return: the html output
        """

        return Truncator(markdownify(str(self.contenu))).chars(comment_truncation, truncate='...', html=True)

    def contenu_all_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return markdownify(str(self.contenu))

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "Commentaire de composant de drone"
        ordering = ['-date']

    def __str__(self):
        return str(self.user) + "_" + str(self.date)


# page de configuration: les configuration et leur commentaires
class DroneConfiguration(models.Model):
    """
    class for describing drone configuration
    """
    version_number = models.CharField(max_length=10,
                                      verbose_name="Numéro de version")
    nick_name = models.CharField(max_length=40, blank=True, default="",
                                 verbose_name="Surnon de la version")
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de realisation")
    Composants = models.ManyToManyField(DroneComponent,
                                verbose_name="Composants du drone")
    version_logiciel = models.CharField(max_length=40, blank=True, default="",
                                        verbose_name="Version du logiciel du contrôleur de vol")
    description = MarkdownxField(blank=True, default="",
                                 verbose_name="Commentaires")
    photo = models.ImageField(null=True, blank=True,
                              upload_to='confimg',
                              verbose_name="Photo de la configuration")

    class Meta:
        """
        Meta data for drone
        """
        verbose_name = "Configuration Drone"
        ordering = ['-date']

    def __str__(self):
        if self.nick_name not in [None, ""]:
            return "Version " + str(self.version_number) + " " + str(self.nick_name)
        return "Version " + str(self.version_number)

    def description_md(self):
        """
        render the description as Markdown
        :return: the html output
        """
        return Truncator(markdownify(str(self.description))).chars(truncation, truncate='...', html=True)

    def description_all_md(self):
        """
        render the description as Markdown
        :return: the html output
        """
        return markdownify(str(self.description))

    def nb_comments(self):
        """
        obtain the number of comments atttached to this model
        :return: the number of comments
        """
        return len(self.get_all_comments())

    def get_comments(self):
        """
        get the last 3 comments
        :return: last tree comments
        """
        return self.get_all_comments()[:3]

    def get_all_comments(self):
        """
        get all comments
        :return: all comments
        """
        return self.comments.filter(active=True)


class ConfigurationComments(models.Model):
    """
    base class for storing comments
    """
    article = models.ForeignKey(DroneConfiguration,
                                on_delete=models.CASCADE,
                                verbose_name="Configuration de drone liée",
                                related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete=models.CASCADE,
                             verbose_name="Auteur du commentaire")
    contenu = MarkdownxField(blank=True, default="",
                             verbose_name="Contenu du commentaire au format Markdown")
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de parution")
    active = models.BooleanField(default=False)

    def contenu_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return Truncator(markdownify(str(self.contenu))).chars(comment_truncation, truncate='...', html=True)

    def contenu_all_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return markdownify(str(self.contenu))

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "Commentaire de configuration de drone"
        ordering = ['-date']

    def __str__(self):
        return str(self.user) + "_" + str(self.date)


# page des vols: les vols (encore en et leur commentaires
class DroneFlight(models.Model):
    """
    class handling drone flights
    """
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de realisation")
    name = models.CharField(max_length=40, blank=True, default="",
                            verbose_name="Titre du vol")
    meteo = models.JSONField(blank=True, default=dict,
                             verbose_name="Definition Météo")
    drone_configuration = models.ForeignKey('DroneConfiguration', on_delete=models.CASCADE,
                                            verbose_name="la configuration de drone utilise")
    summary = MarkdownxField(blank=True,
                             verbose_name="Résumé du vol et observations")
    datalog = models.FileField(blank=True,
                               upload_to="datalog",
                               verbose_name="lien vers le log du vol")
    video = models.FileField(blank=True,
                             upload_to="videoflight",
                             verbose_name="Vidéo du vol")

    class Meta:
        """
        Meta data for drone
        """
        verbose_name = "Vol de  Drone"
        ordering = ['-date']

    def render_meteo(self):
        """
        render the flight weather
        """
        return str(self.meteo)

    def summary_md(self):
        """
        render the summary as Markdown
        :return: the html output
        """
        return Truncator(markdownify(str(self.summary))).chars(truncation, truncate='...', html=True)

    def summary_all_md(self):
        """
        render the summary as Markdown
        :return: the html output
        """
        return markdownify(str(self.summary))

    def nb_comments(self):
        """
        obtain the number of comments atttached to this model
        :return: the number of comments
        """
        return len(self.get_all_comments())

    def get_comments(self):
        """
        get the last 3 comments
        :return: last tree comments
        """
        return self.get_all_comments()[:3]

    def get_all_comments(self):
        """
        get all comments
        :return: all comments
        """
        return self.comments.filter(active=True)

    def __str__(self):
        if self.name not in [None, ""]:
            return str(self.name)
        return "Vol du " + str(self.date)


class FlightComments(models.Model):
    """
    base class for storing comments
    """
    article = models.ForeignKey(DroneFlight,
                                on_delete=models.CASCADE,
                                verbose_name="Article du commentaire",
                                related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, on_delete=models.CASCADE,
                             verbose_name="Auteur du commentaire")
    contenu = MarkdownxField(blank=True, default="",
                             verbose_name="Contenu de l'article au format Markdown")
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de parution")
    active = models.BooleanField(default=False)

    def contenu_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return Truncator(markdownify(str(self.contenu))).chars(comment_truncation, truncate='...', html=True)

    def contenu_all_md(self):
        """
        render the content as Markdown
        :return: the html output
        """
        return markdownify(str(self.contenu))

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "Commentaire de vol"
        ordering = ['-date']

    def __str__(self):
        return str(self.user) + "_" + str(self.date)
