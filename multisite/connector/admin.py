"""Admin Django : le profil utilisateur, inline dans la page `User`."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Le profil, édité depuis la page de l'utilisateur."""

    model = UserProfile
    can_delete = False
    verbose_name = 'Utilisateur'
    verbose_name_plural = 'Utilisateurs'
    fields = ('avatar', 'birthDate', 'user_level')


class UserAdmin(BaseUserAdmin):
    """Admin `User` de Django, augmenté du profil du site."""

    inlines = (UserProfileInline,)


# Réenregistrer User pour attacher l'inline du profil.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
