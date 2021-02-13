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


class PlantationCommentForm(forms.ModelForm):
    """
    Form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = PlantationComment
        fields = ('contenu',)


class PlantsFilterForm(forms.Form):
    """
    formulaire pour filtrer
    """
    nom = forms.CharField(
            label="nom",
            required=False,
    )
    Month_choice = [
        (0, "Tous"),
        (1, "Janvier"),
        (2, "Février"),
        (3, "Mars"),
        (4, "Avril"),
        (5, "Mai"),
        (6, "Juin"),
        (7, "Juillet"),
        (8, "Août"),
        (9, "Septembre"),
        (10, "Octobre"),
        (11, "Novembre"),
        (12, "Décembre"),
    ]
    mois_semi = forms.ChoiceField(
            choices=Month_choice,
            required=False,
            label="Mois de semi",
            initial="Tous",
    )
