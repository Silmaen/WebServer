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
    specifications = models.JSONField(
            default=dict,
            verbose_name="Informations supplémentaires"
    )
    description = MarkdownxField(
            blank=True,
            default="",
            verbose_name="Description de la variété au format Markdown"
    )

    def __str__(self):
        return self.name + " (" + self.vendeur + ")"

    def render_dates(self, classes: str = "plant_date"):
        if ("semis" not in self.specifications) and \
                ("enterre" not in self.specifications) and \
                ("recolte" not in self.specifications and "recolte"):
            return ""
        result = "<table"
        if classes not in ["", None]:
            result += ' class="' + classes + '"'
        result += ">\n"
        result += "<tr><td></td><td>J</td><td>F</td><td>M</td><td>A</td><td>M</td><td>J</td><td>J</td><td>A</td><td>S</td><td>O</td><td>N</td><td>D</td></tr>\n"
        if "semis" in self.specifications:
            result += "<tr><td>Semi sous abris</td>"
            for m in self.specifications["semis"]:
                if m > 0:
                    result += '<td class="semi_actif"></td>'
                else:
                    result += '<td></td>'
            result += "</tr>\n"
        if "enterre" in self.specifications:
            result += "<tr><td>Semi en pleine terre</td>"
            for m in self.specifications["enterre"]:
                if m > 0:
                    result += '<td class="enterre_actif"></td>'
                else:
                    result += '<td></td>'
            result += "</tr>\n"
        if "recolte" in self.specifications:
            result += "<tr><td>Récolte</td>"
            for m in self.specifications["recolte"]:
                if m > 0:
                    result += '<td class="recolte_actif"></td>'
                else:
                    result += '<td></td>'
            result += "</tr>\n"
        result += "</table>\n"
        return result

    def semis_abris_months(self):
        return []

    def semis_terre_months(self):
        return []

    def harvest_months(self):
        return []

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
            null=True,
            verbose_name="Date du semi sous abri")
    SemisTerre = models.DateField(
            blank=True,
            null=True,
            verbose_name="Date du semi en pleine terre")
    Harvested = models.DateField(
            blank=True,
            null=True,
            verbose_name="Date de la récolte")
    Coordinates = models.JSONField(
            verbose_name="liste des coordonnées",
    )
    graine = models.ForeignKey(
            'PlantType',
            on_delete=models.CASCADE,
            verbose_name="Ce qui est planté")
    Commentaires = MarkdownxField(
            blank=True,
            default="",
            verbose_name="Commentaires de cette plantation au format Markdown")

    def commentaire_md(self):
        """
        Rendu tronqué du contenu markdown.
         :return : La sortie html.
        """
        return Truncator(markdownify(str(self.Commentaires))).chars(truncation, truncate='...', html=True)

    def commentaire_all_md(self):
        """
        Rendu complet du contenu markdown.
         :return : La sortie html.
        """
        return markdownify(str(self.Commentaires))

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

    def is_harvested(self):
        """
        renvoie si cette récolte a déjà été ramassée
        :return: True si déjà ramassé
        """
        now = timezone.now().date()
        if self.Harvested not in ["", None]:
            if self.Harvested < now:
                return True
        return False

    def is_in_potager(self):
        """
        Est-ce que le plant est encore dans le potager?
        """
        now = timezone.now()
        if self.SemisTerre in ["", None]:  # s'il n'y a pas de date de semi en terre, alors pas dans le potager
            return False
        if self.SemisTerre > now:  # si la date de semis est plus tard que maintenant, alors pas dans le potager
            return False
        return not self.is_harvested()

    def display_in_potager(self):
        """
        Est-ce que le plant est dans le potager ou est planifié
        """
        if self.SemisTerre in ["", None]:
            return False
        return not self.is_harvested()

    def is_at_coord(self, row: int, col: int):
        """
        check the location
        """
        if "coords" not in self.Coordinates:
            return False
        for cc in self.Coordinates["coords"]:
            if cc[0] == col and cc[1] == row:
                return True
        return False

    def get_coord_list(self):
        if "coords" not in self.Coordinates:
            return []
        return self.Coordinates["coords"]


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