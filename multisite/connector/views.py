"""Fichier main.users.users_view.py les vues users."""
from django.contrib.auth import login
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, reverse
from .forms import CustomUserCreationForm, CustomUserChangeForm, ProfileForm
from . import settings


def profile(request):
    """User wants to view its profile."""
    if request.user.is_authenticated:
        return render(request, "registration/profile.html", {
            **settings.base_info, "user": request.user
        })
    else:
        return register(request)


def register(request):
    """Register new user."""
    good = True
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        profile_form = ProfileForm(request.POST, instance=request.user.userprofile)
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            profile_form.save()
            login(request, user)
            return redirect(reverse("news"))
        good = False
    return render(request, "registration/register.html",
                  {**settings.base_info, "form": CustomUserCreationForm, "profile_form": ProfileForm, "is_good": good})


def profile_edit(request):
    """
    User wants to edit its profile.
    """
    good = True
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user.userprofile)
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            return redirect(reverse("profile"))
        good = False
    else:
        form = CustomUserChangeForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user)
    return render(request, "registration/profile_change.html",
                  {**settings.base_info, "form": form, "profile_form": profile_form, "is_good": good})


class CustomPasswordResetView(PasswordResetView):
    """
    Custom class for password reset.
    """
    from_email = "webmaster@argawaen.net"
    html_email_template_name = 'registration/password_reset_email.html'
