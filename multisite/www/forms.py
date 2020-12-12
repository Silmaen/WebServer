"""Formulaire pour le drone"""
from .models import *
from markdownx.forms import forms


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
