"""main.forms"""
from django.contrib.auth.forms import UserCreationForm
# from django import forms
from .models import *
from markdownx.forms import forms


class CustomUserCreationForm(UserCreationForm):
    """
    form fo user creation
    """
    class Meta(UserCreationForm.Meta):
        """
        Meta informations
        """
        fields = UserCreationForm.Meta.fields + ("first_name", "last_name", "email")


class ArticleCommentForm(forms.ModelForm):
    """
    form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = ArticleComments
        fields = ('contenu',)


class DroneComponentCommentForm(forms.ModelForm):
    """
    form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = DroneComponentComments
        fields = ('contenu',)


class DroneConfigurationCommentForm(forms.ModelForm):
    """
    form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = ConfigurationComments
        fields = ('contenu',)


class DroneFlightCommentForm(forms.ModelForm):
    """
    form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = FlightComments
        fields = ('contenu',)
