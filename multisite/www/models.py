"""model.py exemple de profile user"""
import ipaddress
import socket

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.html import escape, mark_safe
from django.utils.text import Truncator

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


class BricolageArticle(models.Model):
    """Article de bricolage."""
    titre = models.CharField(max_length=150, verbose_name="Titre")
    slug = models.SlugField(max_length=150, unique=True)
    contenu = MarkdownxField(blank=True, default="", verbose_name="Contenu")
    date = models.DateField(verbose_name="Date")

    class Meta:
        """Meta data"""
        ordering = ["-date"]
        verbose_name = "article de bricolage"
        verbose_name_plural = "articles de bricolage"

    def __str__(self):
        return self.titre

    def contenu_md(self):
        """Retourne le contenu complet converti en HTML."""
        return markdownify(self.contenu)

    def resume_md(self):
        """Retourne un résumé tronqué du contenu HTML (200 caractères)."""
        return Truncator(markdownify(self.contenu)).chars(200, truncate="…", html=True)


class ServiceCategorie(models.Model):
    """Catégorie de service."""
    nom = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    mdi_icon_name = models.CharField(max_length=30, blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        """Meta data"""
        ordering = ["ordre", "nom"]
        verbose_name = "catégorie de service"
        verbose_name_plural = "catégories de service"

    def __str__(self):
        return self.nom


RESEAU_LOCAL = ipaddress.ip_network("10.10.0.0/16")


class Machine(models.Model):
    """Machine réseau à monitorer. Le nom sert de hostname."""
    nom = models.CharField(max_length=100, verbose_name="Nom / Hostname")
    categorie = models.ForeignKey(
        ServiceCategorie, on_delete=models.CASCADE,
        related_name="machines", verbose_name="Catégorie")
    adresse_ip = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="Adresse IP")
    ip_statique = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="IP statique attendue")
    alerte_ip = models.CharField(
        max_length=300, blank=True, verbose_name="Alerte IP")
    ports_supplementaires = models.CharField(
        max_length=200, blank=True,
        verbose_name="Ports supplémentaires",
        help_text="Ports ou plages à scanner en plus des ports courants (ex: 8080,9000-9100)")
    en_ligne = models.BooleanField(default=False, verbose_name="En ligne")
    derniere_verification = models.DateTimeField(null=True, blank=True)
    derniere_vue_en_ligne = models.DateTimeField(null=True, blank=True)
    ports_ouverts = models.JSONField(default=list, blank=True, verbose_name="Ports ouverts")
    dernier_scan_ports = models.DateTimeField(null=True, blank=True, verbose_name="Dernier scan ports")

    class Meta:
        """Meta data"""
        ordering = ["categorie__ordre", "nom"]
        verbose_name = "machine"
        verbose_name_plural = "machines"

    def __str__(self):
        if self.adresse_ip:
            return f"{self.nom} ({self.adresse_ip})"
        return self.nom

    def hostname_complet(self):
        """Retourne le nom avec le domaine par défaut si nécessaire."""
        if "." in self.nom:
            return self.nom
        domaine = getattr(settings, "MONITORING_DOMAINE_DEFAUT", "")
        if domaine:
            return f"{self.nom}.{domaine}"
        return self.nom

    def resoudre_ip(self):
        """
        Résout l'IP via DNS à partir du nom (hostname).
        :return : Tuple (ip, alerte) — ip peut être None en cas d'échec.
        """
        fqdn = self.hostname_complet()
        alerte = ""
        try:
            ip_resolue = socket.gethostbyname(fqdn)
        except socket.gaierror:
            return None, f"Résolution DNS impossible pour {fqdn}"

        # Vérifier que l'IP est dans le réseau local
        try:
            if ipaddress.ip_address(ip_resolue) not in RESEAU_LOCAL:
                return ip_resolue, f"L'IP résolue {ip_resolue} est hors du réseau {RESEAU_LOCAL}"
        except ValueError:
            return None, f"IP résolue invalide : {ip_resolue}"

        # Vérifier la cohérence avec ip_statique
        if self.ip_statique and ip_resolue != self.ip_statique:
            alerte = f"IP résolue ({ip_resolue}) différente de l'IP statique attendue ({self.ip_statique})"

        return ip_resolue, alerte

    def clean(self):
        """Valide que l'IP statique est dans le réseau local 10.10.0.0/16."""
        super().clean()
        if self.ip_statique:
            try:
                ip = ipaddress.ip_address(self.ip_statique)
            except ValueError:
                raise ValidationError({"ip_statique": "Adresse IP invalide."})
            if ip not in RESEAU_LOCAL:
                raise ValidationError({
                    "ip_statique": f"L'adresse doit être dans le réseau {RESEAU_LOCAL}."
                })


class Serveur(models.Model):
    """Serveur web à monitorer."""
    titre = models.CharField(max_length=100)
    categorie = models.ForeignKey(
        ServiceCategorie, on_delete=models.CASCADE,
        related_name="serveurs", verbose_name="Catégorie")
    description = models.CharField(max_length=200, blank=True, verbose_name="Description")
    url = models.URLField(blank=True, verbose_name="URL du service")
    hostname = models.CharField(max_length=200, blank=True, verbose_name="Hostname")
    adresse = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP")
    port = models.PositiveIntegerField(null=True, blank=True, verbose_name="Port")
    en_ligne = models.BooleanField(default=False, verbose_name="En ligne")
    reverse_proxy_ok = models.BooleanField(default=False, verbose_name="Reverse proxy OK")
    derniere_verification = models.DateTimeField(null=True, blank=True)
    derniere_vue_en_ligne = models.DateTimeField(null=True, blank=True)
    mdi_icon_name = models.CharField(max_length=30, blank=True)
    icone_image = models.ImageField(
        blank=True, upload_to="service_icones", verbose_name="Icône (image)")
    icone_url = models.URLField(blank=True, verbose_name="Icône (URL)")

    class Meta:
        """Meta data"""
        ordering = ["categorie__ordre", "titre"]
        verbose_name = "serveur"
        verbose_name_plural = "serveurs"

    def __str__(self):
        return self.titre

    def has_icone(self):
        """Vérifie si le serveur possède une icône."""
        return bool(self.mdi_icon_name or self.icone_image or self.icone_url)

    def icone_html(self):
        """Retourne le HTML de l'icône selon le mode actif."""
        if self.icone_image:
            return mark_safe(f'<img src="{escape(self.icone_image.url)}" class="service-icone-img">')
        if self.icone_url:
            return mark_safe(f'<img src="{escape(self.icone_url)}" class="service-icone-img">')
        if self.mdi_icon_name:
            return mark_safe(f'<span class="mdi mdi-{escape(self.mdi_icon_name)}"></span>')
        return ""

    def lien(self):
        """Retourne l'URL principale pour accéder au serveur."""
        if self.url:
            return self.url
        hote = self.adresse or self.hostname
        if hote and self.port:
            return f"http://{hote}:{self.port}"
        return ""

    def adresse_effective(self):
        """Retourne l'adresse IP ou le hostname pour les vérifications."""
        return self.adresse or self.hostname

    def clean(self):
        """Valide qu'au moins url ou (adresse/hostname+port) est fourni."""
        super().clean()
        hote = self.adresse or self.hostname
        if not self.url and not (hote and self.port):
            raise ValidationError(
                "Il faut fournir au moins une URL ou une adresse (IP/hostname) + port."
            )
