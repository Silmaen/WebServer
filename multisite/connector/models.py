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
        """Enregistre le profil, puis derive `User.is_staff` de son niveau.

        Le niveau est la source de verite, `is_staff` en est deduit : une seule
        direction, et c'est ce qui rend le resultat previsible.

        Ce n'etait pas le cas avant. Un second recepteur `post_save` sur `User`
        appelait `instance.userprofile.save()`, donc enregistrer un profil sauvait
        l'utilisateur, ce qui reenregistrait le profil -- parfois une instance
        perimee, chargee avant la modification, qui reecrivait alors l'ancien niveau.
        Symptome observe : poser `user_level = 3`, sauver, relire 0, avec `is_staff`
        pourtant passe a True. Le recepteur ne fait plus que garantir l'existence du
        profil, il ne le reenregistre jamais.
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
    """Garantit qu'un `User` a un profil, sans jamais reenregistrer celui qui existe.

    Remplace les deux recepteurs precedents. Celui qui reenregistrait le profil a
    chaque sauvegarde d'utilisateur formait une boucle avec `UserProfile.save()` --
    voir l'explication la-bas. Creer ce qui manque suffit : un niveau n'a pas besoin
    d'etre reecrit pour rester ce qu'il est.

    La branche sans `created` couvre les comptes importes, anterieurs a l'obligation
    de profil : sans elle, le context processor de navigation leve une exception sur
    chacune de leurs pages.
    """
    if created or not UserProfile.objects.filter(user=instance).exists():
        UserProfile.objects.get_or_create(user=instance)
