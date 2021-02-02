from django.db import models
from markdownx.utils import markdownify
from django.conf import settings
from django.utils.text import Truncator

# Create your models here.
from markdownx.models import MarkdownxField
from django.utils import timezone

strMois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
truncation = 200  # Longueur de la troncature dans les articles
comment_truncation = 100  # Longueur de la troncature dans les commentaires
nb_last_comments = 3  # Le nombre de commentaires à renvoyer en mode tronqué


def intToMonthStrList(mcode: int):
    """
    Convert month code to string list of months
    :param mcode: month code
    :return: list of month name
    """
    res = []
    for i, m in enumerate(strMois):
        if mcode & (1 << i):
            res.append(m)
    return res


def intToMonthIdList(mcode: int):
    """
    Convert month code to id list of months
    :param mcode: month code
    :return: list of month id (1 for the first month)
    """
    res = []
    for i in range(len(strMois)):
        if mcode & (1 << i):
            res.append(i+1)
    return res


def monthListTomcode(months: list):
    """
    convert a month list into month code
    :param months: list of month (name or month number)
    :return: the month code
    """
    res = 0
    for m in months:
        if type(m) == int:
            if m < 0 or m > 12:  # bad number
                continue
            res |= 1 << (m-1)
        if type(m) == str:
            if m not in strMois:  # bad name
                continue
            res |= 1 << strMois.index(m)
    return res


def addMonthTomcode(mcode:int, month: int):
    mcode |= (1 << month)
    return mcode


class PlantType(models.Model):
    """
    Variété de plant
    """
    name = models.CharField(
            max_length=60,
            verbose_name="Nom de variété")
    vendeur = models.CharField(
            max_length=60,
            verbose_name="Nom du vendeur")
    icon = models.CharField(
            max_length=30,
            blank=True,
            default="",
            verbose_name="nom de l'icône")
    semis_abris = models.PositiveSmallIntegerField(
            verbose_name="Mois de semis sous abris",
            blank=True,
            default=0,
    )
    semis_terre = models.PositiveSmallIntegerField(
            verbose_name="Mois de semis en pleine terre",
            blank=True,
            default=0,
    )
    harvest = models.PositiveSmallIntegerField(
            verbose_name="Mois de récolte",
            blank=True,
            default=0,
    )
    description = MarkdownxField(
            blank=True,
            default="",
            verbose_name="Description de la variété au format Markdown"
    )

    def semis_abris_months(self):
        return intToMonthStrList(self.semis_abris)

    def semis_terre_months(self):
        return intToMonthStrList(self.semis_terre)

    def harvest_months(self):
        return intToMonthStrList(self.harvest)

    def description_md(self):
        """
        Rendu tronqué du contenu markdown.
         :return : La sortie html.
        """
        return Truncator(markdownify(str(self.description))).chars(truncation, truncate='...', html=True)

    def description_all_md(self):
        """
        Rendu complet du contenu markdown.
         :return : La sortie html.
        """
        return markdownify(str(self.description))

    def nb_comments(self):
        """
        Obtient le nombre de commentaires associés à l’article.
         :return : Nombre de commentaires.
        """
        return len(self.get_all_comments())

    def get_comments(self):
        """
        Fonction qui renvoie les `nb_last_comments` derniers commentaires.
         :return : Les nb_last_comments derniers commentaires.
        """
        return self.get_all_comments()[:nb_last_comments]

    def get_all_comments(self):
        """
        Renvoie la liste de tous les commentaires.
         :return : Tous les commentaires
        """
        return self.comments.filter(active=True).order_by("-date")


class PlantTypeComment(models.Model):
    """
    Objet de stockage des commentaires sur les types de plantation
    """
    type_plant = models.ForeignKey(
        PlantType, on_delete=models.CASCADE,
        verbose_name="Plant lié",
        related_name="comments")
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, editable=False, on_delete=models.CASCADE,
        verbose_name="Auteur du commentaire")
    contenu = MarkdownxField(
        blank=True, default="",
        verbose_name="Contenu du commentaire au format Markdown")
    date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de parution")
    active = models.BooleanField(
        default=False)

    def contenu_md(self):
        """
        Rendu tronqué du contenu markdown.
         :return : La sortie html.
        """
        return Truncator(markdownify(str(self.contenu))).chars(40, truncate='...', html=True)

    def contenu_all_md(self):
        """
        Rendu complet du contenu markdown.
         :return : La sortie html.
        """
        return markdownify(str(self.contenu))

    class Meta:
        """
        Meta data
        """
        verbose_name = "Commentaire de plant"
        ordering = ['-date']

    def __str__(self):
        return str(self.auteur) + "_" + str(self.date)


class Plantation(models.Model):
    """
    description d'une plantation
    """
    Semis = models.DateField(
            blank=True,
            verbose_name="Date du semi sous abri")
    SemisTerre = models.DateField(
            blank=True,
            verbose_name="Date du semi en pleine terre")
    Harvested = models.DateField(
            blank=True,
            verbose_name="Date de la récolte")
    CoordX = models.PositiveIntegerField(
            default=0,
            verbose_name="Placement en X")
    CoordY = models.PositiveIntegerField(
            default=0,
            verbose_name="Placement en Y")
    Commentaires = MarkdownxField(
            blank=True,
            default="",
            verbose_name="Commentaires de cette plantation au format Markdown"
    )

    def commentaire_md(self):
        """
        Rendu complet du contenu markdown.
         :return : La sortie html.
        """
        return markdownify(str(self.Commentaires))

    def is_in_potager(self):
        """
        Est-ce que le plant est encore dans le potager?
        """
        now = timezone.now()
        if self.SemisTerre == "":
            return False
        if self.SemisTerre > now:
            return False
        if self.Harvested != "":
            if self.Harvested < now:
                return False
        return True


class PlantationComment(models.Model):
    """
    Objet de stockage des commentaires sur les plantations
    """
    plantation = models.ForeignKey(
        Plantation, on_delete=models.CASCADE,
        verbose_name="Plantation lié",
        related_name="comments")
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, editable=False, on_delete=models.CASCADE,
        verbose_name="Auteur du commentaire")
    contenu = MarkdownxField(
        blank=True, default="",
        verbose_name="Contenu du commentaire au format Markdown")
    date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de parution")
    active = models.BooleanField(
        default=False)

    def contenu_md(self):
        """
        Rendu tronqué du contenu markdown.
         :return : La sortie html.
        """
        return Truncator(markdownify(str(self.contenu))).chars(40, truncate='...', html=True)

    def contenu_all_md(self):
        """
        Rendu complet du contenu markdown.
         :return : La sortie html.
        """
        return markdownify(str(self.contenu))

    class Meta:
        """
        Meta data
        """
        verbose_name = "Commentaire de plant"
        ordering = ['-date']

    def __str__(self):
        return str(self.auteur) + "_" + str(self.date)