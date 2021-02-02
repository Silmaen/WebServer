"""Formulaire pour le drone"""
from .models import *
from markdownx.forms import forms


class PlantTypeCommentForm(forms.ModelForm):
    """
    Form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = PlantTypeComment
        fields = ('contenu',)
