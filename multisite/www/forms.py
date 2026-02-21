"""Formulaire pour le site www"""
from django import forms as django_forms
from django.db.models import Max
from django.utils.text import slugify

from markdownx.forms import forms

from .models import ArticleComment, ProjetCategorie, Projet, BricolageArticle, ServiceCategorie, Machine, Serveur
from .widgets import MdiIconPickerWidget, ColorPickerWidget


class ArticleCommentForm(forms.ModelForm):
    """
    Form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = ArticleComment
        fields = ('contenu',)


class ProjetCategorieForm(forms.ModelForm):
    """Formulaire pour les catégories de projet."""
    class Meta:
        """Meta informations"""
        model = ProjetCategorie
        exclude = ("slug",)
        widgets = {
            "mdi_icon_name": MdiIconPickerWidget(),
        }

    def __init__(self, *args, **kwargs):
        """Pré-remplit l'ordre pour les nouvelles catégories."""
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            max_ordre = ProjetCategorie.objects.aggregate(m=Max("ordre"))["m"]
            self.fields["ordre"].initial = (max_ordre or 0) + 1

    def save(self, commit=True):
        """Auto-génère le slug à la création."""
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.nom)
        if commit:
            instance.save()
        return instance


class ProjetForm(forms.ModelForm):
    """Formulaire pour les projets."""
    class Meta:
        """Meta informations"""
        model = Projet
        exclude = ("slug",)
        widgets = {
            "mdi_icon_name": MdiIconPickerWidget(),
            "couleur": ColorPickerWidget(),
            "date_creation": django_forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "icone_image": django_forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "icone_url": django_forms.URLInput(),
        }

    def __init__(self, *args, **kwargs):
        """Pré-remplit l'ordre pour les nouveaux projets."""
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            max_ordre = Projet.objects.aggregate(m=Max("ordre"))["m"]
            self.fields["ordre"].initial = (max_ordre or 0) + 1

    def clean(self):
        """Valide qu'un seul mode d'icône est actif à la fois."""
        cleaned = super().clean()
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
        return cleaned

    def save(self, commit=True):
        """Auto-génère le slug et nettoie les champs icône inactifs."""
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.titre)
        # Nettoyage : un seul mode d'icône actif
        if instance.mdi_icon_name:
            instance.icone_image = ""
            instance.icone_url = ""
        elif instance.icone_image:
            instance.mdi_icon_name = ""
            instance.icone_url = ""
        elif instance.icone_url:
            instance.mdi_icon_name = ""
            instance.icone_image = ""
        if commit:
            instance.save()
        return instance


class ServiceCategorieForm(forms.ModelForm):
    """Formulaire pour les catégories de service."""
    class Meta:
        """Meta informations"""
        model = ServiceCategorie
        exclude = ("slug",)
        widgets = {
            "mdi_icon_name": MdiIconPickerWidget(),
        }

    def __init__(self, *args, **kwargs):
        """Pré-remplit l'ordre pour les nouvelles catégories."""
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            max_ordre = ServiceCategorie.objects.aggregate(m=Max("ordre"))["m"]
            self.fields["ordre"].initial = (max_ordre or 0) + 1

    def save(self, commit=True):
        """Auto-génère le slug à la création."""
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.nom)
        if commit:
            instance.save()
        return instance


class MachineForm(forms.ModelForm):
    """Formulaire pour les machines réseau."""
    class Meta:
        """Meta informations"""
        model = Machine
        fields = ("nom", "categorie", "ip_statique", "ports_supplementaires")


class ServeurForm(forms.ModelForm):
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
        url = cleaned.get("url")
        adresse = cleaned.get("adresse")
        hostname = cleaned.get("hostname")
        port = cleaned.get("port")
        hote = adresse or hostname
        if not url and not (hote and port):
            raise django_forms.ValidationError(
                "Il faut fournir au moins une URL ou une adresse (IP/hostname) + port."
            )
        return cleaned

    def save(self, commit=True):
        """Nettoie les champs icône inactifs."""
        instance = super().save(commit=False)
        if instance.mdi_icon_name:
            instance.icone_image = ""
            instance.icone_url = ""
        elif instance.icone_image:
            instance.mdi_icon_name = ""
            instance.icone_url = ""
        elif instance.icone_url:
            instance.mdi_icon_name = ""
            instance.icone_image = ""
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
