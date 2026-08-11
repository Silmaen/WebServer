"""Formulaires du site www."""
from django import forms as django_forms
from django.db.models import Max
from django.utils.text import slugify

from markdownx.forms import forms

from .models import (
    ArticleComment, BricolageArticle, Machine, Projet, ProjetCategorie,
    Serveur, ServiceCategorie,
)
from .widgets import ColorPickerWidget, MdiIconPickerWidget


class IconeModeMixin:
    """Un seul mode d'icône actif à la fois : MDI, image ou URL.

    Le modèle porte les trois champs pour laisser le choix à la saisie ; ce mixin
    interdit d'en remplir plusieurs et vide les autres à l'enregistrement, afin que
    `icone_html()` n'ait pas à arbitrer.
    """

    def valider_mode_icone(self, cleaned):
        """Lève une erreur si plus d'un mode d'icône est renseigné."""
        modes = []
        if cleaned.get("mdi_icon_name"):
            modes.append("MDI")
        if cleaned.get("icone_image"):
            modes.append("Image")
        if cleaned.get("icone_url"):
            modes.append("URL")
        if len(modes) > 1:
            raise django_forms.ValidationError(
                "Un seul mode d'icône peut être actif à la fois "
                f"({', '.join(modes)} sélectionnés)."
            )

    @staticmethod
    def nettoyer_icones(instance):
        """Vide les champs d'icône que le mode retenu n'utilise pas."""
        if instance.mdi_icon_name:
            instance.icone_image = ""
            instance.icone_url = ""
        elif instance.icone_image:
            instance.mdi_icon_name = ""
            instance.icone_url = ""
        elif instance.icone_url:
            instance.mdi_icon_name = ""
            instance.icone_image = ""


class AutoSlugOrdreMixin:
    """Génère le slug et la position à la création, tous deux exclus du formulaire."""

    def appliquer_slug_et_ordre(self, instance, source):
        """Pose le slug depuis `source` et l'ordre à la suite du dernier."""
        if not instance.slug:
            instance.slug = slugify(source)
        if not instance.pk:
            max_ordre = self.Meta.model.objects.aggregate(m=Max("ordre"))["m"]
            instance.ordre = (max_ordre or 0) + 1


class ArticleCommentForm(forms.ModelForm):
    """Formulaire de création d'un commentaire d'article."""
    class Meta:
        """Meta informations"""
        model = ArticleComment
        fields = ('contenu',)


class ProjetCategorieForm(AutoSlugOrdreMixin, forms.ModelForm):
    """Formulaire pour les catégories de projet."""
    class Meta:
        """Meta informations"""
        model = ProjetCategorie
        exclude = ("slug", "ordre")
        widgets = {
            "mdi_icon_name": MdiIconPickerWidget(),
        }

    def save(self, commit=True):
        """Auto-génère le slug et l'ordre à la création."""
        instance = super().save(commit=False)
        self.appliquer_slug_et_ordre(instance, instance.nom)
        if commit:
            instance.save()
        return instance


class ProjetForm(IconeModeMixin, AutoSlugOrdreMixin, forms.ModelForm):
    """Formulaire pour les projets."""
    class Meta:
        """Meta informations"""
        model = Projet
        exclude = ("slug", "ordre")
        widgets = {
            "mdi_icon_name": MdiIconPickerWidget(),
            "couleur": ColorPickerWidget(),
            "date_creation": django_forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "icone_image": django_forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "icone_url": django_forms.URLInput(),
        }

    def clean(self):
        """Valide qu'un seul mode d'icône est actif à la fois."""
        cleaned = super().clean()
        self.valider_mode_icone(cleaned)
        return cleaned

    def save(self, commit=True):
        """Auto-génère le slug, l'ordre et nettoie les champs icône inactifs."""
        instance = super().save(commit=False)
        self.appliquer_slug_et_ordre(instance, instance.titre)
        self.nettoyer_icones(instance)
        if commit:
            instance.save()
        return instance


class ServiceCategorieForm(AutoSlugOrdreMixin, forms.ModelForm):
    """Formulaire pour les catégories de service."""
    class Meta:
        """Meta informations"""
        model = ServiceCategorie
        exclude = ("slug", "ordre")
        widgets = {
            "mdi_icon_name": MdiIconPickerWidget(),
        }

    def save(self, commit=True):
        """Auto-génère le slug et l'ordre à la création."""
        instance = super().save(commit=False)
        self.appliquer_slug_et_ordre(instance, instance.nom)
        if commit:
            instance.save()
        return instance


class MachineForm(forms.ModelForm):
    """Formulaire pour les machines réseau."""
    class Meta:
        """Meta informations"""
        model = Machine
        fields = ("nom", "categorie", "ip_statique", "ports_supplementaires")


class ServeurForm(IconeModeMixin, forms.ModelForm):
    """Formulaire pour les serveurs."""
    class Meta:
        """Meta informations"""
        model = Serveur
        fields = (
            "titre", "categorie", "description",
            "url", "hostname", "adresse", "port",
            "mdi_icon_name", "icone_image", "icone_url",
        )
        widgets = {
            "mdi_icon_name": MdiIconPickerWidget(),
            "icone_image": django_forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "icone_url": django_forms.URLInput(),
        }

    def clean(self):
        """Valide un seul mode d'icône et au moins url ou adresse+port."""
        cleaned = super().clean()
        self.valider_mode_icone(cleaned)
        url = cleaned.get("url")
        hote = cleaned.get("adresse") or cleaned.get("hostname")
        if not url and not (hote and cleaned.get("port")):
            raise django_forms.ValidationError(
                "Il faut fournir au moins une URL ou une adresse (IP/hostname) + port."
            )
        return cleaned

    def save(self, commit=True):
        """Nettoie les champs icône inactifs."""
        instance = super().save(commit=False)
        self.nettoyer_icones(instance)
        if commit:
            instance.save()
        return instance


class BricolageArticleForm(forms.ModelForm):
    """Formulaire pour les articles de bricolage."""
    class Meta:
        """Meta informations"""
        model = BricolageArticle
        exclude = ("slug",)
        widgets = {
            "date": django_forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

    def save(self, commit=True):
        """Auto-génère le slug à la création."""
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.titre)
        if commit:
            instance.save()
        return instance
