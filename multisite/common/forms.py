"""Formulaire pour les parties communes"""
from markdownx.forms import forms
from .models import SiteArticleComment


class SiteArticleCommentForm(forms.ModelForm):
    """
    Form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = SiteArticleComment
        fields = ('contenu',)
