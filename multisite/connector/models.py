"""Profil utilisateur du site : avatar, date de naissance et niveau d'accès."""
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from common.user_utils import ADMINISTRATEUR, ENREGISTRE, USER_LEVEL_CHOICES


class UserProfile(models.Model):
    """Profil utilisateur, créé automatiquement pour chaque `User`."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    avatar = models.ImageField(
        blank=True, null=True, verbose_name="avatar", upload_to='user_avatar')
    birthDate = models.DateField(blank=True, null=True, verbose_name="date de naissance")
    user_level = models.IntegerField(
        choices=USER_LEVEL_CHOICES,
        default=ENREGISTRE,
        verbose_name="niveau utilisateur",
    )

    class Meta:
        """Meta data"""
        verbose_name = "profil utilisateur"
        verbose_name_plural = "profils utilisateurs"

    def __str__(self):
        """Nom d'utilisateur et niveau d'accès."""
        return f"{self.user.username} ({self.get_user_level_display()})"

    def save(self, *args, **kwargs):
        """Enregistre le profil, puis dérive `User.is_staff` de son niveau.

        Le niveau est la source de vérité et `is_staff` en est déduit : une seule
        direction, ce qui rend le résultat prévisible. Le sens inverse formait une
        boucle avec le récepteur `post_save`, qui pouvait réécrire l'ancien niveau
        depuis une instance périmée.
        """
        if not self.user_id:
            super().save(*args, **kwargs)
            return
        if self.user.is_superuser and self.user_level < ADMINISTRATEUR:
            self.user_level = ADMINISTRATEUR
        super().save(*args, **kwargs)
        expected_staff = self.user_level >= ADMINISTRATEUR
        if not self.user.is_superuser and self.user.is_staff != expected_staff:
            self.user.is_staff = expected_staff
            self.user.save(update_fields=['is_staff'])


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    """Garantit qu'un `User` a un profil, sans jamais réenregistrer celui qui existe.

    Réenregistrer le profil formerait une boucle avec `UserProfile.save()`. La branche
    sans `created` couvre les comptes importés, antérieurs à l'obligation de profil :
    sans elle, le context processor de navigation lève une exception sur leurs pages.
    """
    if created or not UserProfile.objects.filter(user=instance).exists():
        UserProfile.objects.get_or_create(user=instance)
