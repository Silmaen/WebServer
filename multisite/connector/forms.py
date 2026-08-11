"""Formulaires de compte et de profil utilisateur."""
from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Formulaire de création d’un utilisateur, avec nom et adresse."""

    class Meta(UserCreationForm.Meta):
        """Meta informations"""
        fields = UserCreationForm.Meta.fields + ("first_name", "last_name", "email")

    def save(self, commit=True):
        """Reporte nom, prénom et adresse sur l'utilisateur créé."""
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Formulaire des informations de profil : avatar et date de naissance."""

    class Meta:
        """Meta informations"""
        model = UserProfile
        fields = ('avatar', 'birthDate')


class CustomUserChangeForm(UserChangeForm):
    """Formulaire de modification des informations de compte."""

    class Meta(UserChangeForm.Meta):
        """Meta informations"""
        fields = ('first_name', 'last_name', 'email')
