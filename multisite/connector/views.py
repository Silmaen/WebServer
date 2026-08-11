"""Vues d'authentification, d'inscription et de profil."""
from django.contrib.auth import login
from django.contrib.auth.views import PasswordResetView
from django.shortcuts import redirect, render

from . import settings
from .forms import CustomUserChangeForm, CustomUserCreationForm, ProfileForm


def profile(request):
    """
    Page de profil ; propose l'inscription à un visiteur anonyme.
     :param request : La requête du client.
     :return : La page rendue.
    """
    if request.user.is_authenticated:
        return render(request, "registration/profile.html", {
            **settings.base_info, "user": request.user
        })
    else:
        return register(request)


def register(request):
    """
    Inscription d'un nouvel utilisateur, connecté aussitôt.
     :param request : La requête du client.
     :return : La page rendue ou une redirection vers l'accueil.
    """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            profile_form.save()
            login(request, user)
            return redirect("accueil")
        return render(request, "registration/register.html", {
            **settings.base_info,
            "form": form,
            "profile_form": profile_form
        })
    else:
        return render(request, "registration/register.html", {
            **settings.base_info,
            "form": CustomUserCreationForm,
            "profile_form": ProfileForm
        })


def profile_edit(request):
    """
    Modification du profil et des informations de compte.
     :param request : La requête du client.
     :return : La page rendue ou une redirection vers le profil.
    """
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            return redirect("profile")
    else:
        form = CustomUserChangeForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.userprofile)
    return render(request, "registration/profile_change.html", {
        **settings.base_info,
        "form": form,
        "profile_form": profile_form
    })


class CustomPasswordResetView(PasswordResetView):
    """Réinitialisation du mot de passe, avec un courriel au format HTML."""

    html_email_template_name = 'registration/password_reset_email.html'
