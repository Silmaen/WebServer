"""users.models"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class AccessPermission(models.Model):
    """
    un attribut special permettant les acces d'un user dans differentes parties du site
    """
    nom = models.CharField(max_length=30)
    description = models.TextField(null=True)

    def __str__(self):
        return self.nom


class CustomUser(AbstractUser):
    """
    un user custom pour pouvoir ajouter des champs
    fiels from AbstractUser / and other:
     - username
     - password
     - first_name
     - last_name
     - is_staff (could log in the admin section)
     - is_active
     - date_joined
     - last_login
     - is_superuser
     - groups
     - user_permissions
    """
    avatar = models.ImageField(upload_to="UserAvatar/", blank=True)
    AccessPermissions = models.ManyToManyField(AccessPermission)

    @property
    def has_Developper_Access(self):
        for f in self.AccessPermissions.all():
            if "See_developper_pages" in f.nom:
                return True
        return False

    @property
    def has_Hidden_Access(self):
        for f in self.AccessPermissions.all():
            if "Access_hidden_news" in f.nom:
                return True
        return False

    def __str__(self):
        return self.username
