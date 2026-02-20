"""Fichier UserProfile.models.py pour les mod\u00e8les d'utilisateurs"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from common.user_utils import ENREGISTRE, ADMINISTRATEUR, USER_LEVEL_CHOICES


class UserProfile(models.Model):
    """Profil utilisateur avec niveau d'acc\u00e8s"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    avatar = models.ImageField(blank=True, null=True, verbose_name="avatar", upload_to='user_avatar')
    birthDate = models.DateField(blank=True, null=True, verbose_name="date de naissance")
    user_level = models.IntegerField(
        choices=USER_LEVEL_CHOICES,
        default=ENREGISTRE,
        verbose_name="niveau utilisateur",
    )

    def save(self, *args, **kwargs):
        """Synchronise user_level et User.is_staff."""
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
def create_user_profile(sender, instance, created, **kwargs):
    """Lorsque l'on cr\u00e9e un `User`, cela cr\u00e9e un profil aussi."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Lorsque l'on sauve un `User` on le fait aussi pour son profil."""
    instance.userprofile.save()
