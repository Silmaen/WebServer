"""Formulaire pour les parties communes"""
from markdownx.forms import forms
from .models import SiteArticleComment


class SiteArticleCommentForm(forms.ModelForm):
    """Formulaire de création d'un commentaire d'article."""

    class Meta:
        """Meta informations"""
        model = SiteArticleComment
        fields = ('contenu',)
