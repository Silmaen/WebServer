# Site web argawaen.net

## Introduction

Ce dépôt a pour vocation a devenir le principal gestionnaire des sites du domaine argawaen.net.

### Liste des objectifs initiaux

* Avoir du texte stocké dans la base au format markdown
* Avoir un utilisateur avec un profil attaché
* Permettre l’utilisation de virtual hosts pour distribuer plusieurs sites
* Avoir une base d’utilisateurs partagés entre plusieurs sites
    * voir à partager du code

### Liste des sites distribués (virtual host)

Tous les sites ont pour domaine `argawaen.net`, on ne notera ici que leur préfixe :

* [www](https://www.argawaen.net) le site principal.


## L’implémentation

### Modules django

Liste des modules installés :

* Django (base framework)
* Pillow (Image management)
* mysqlclient (pour que Django soit capable de se connecter à la base MySQL)
* django-markdownx (render mark down)
* html5lib-truncation (allow truncation on html text to make summary)

Commande :

```bash
python -m pip install Django Pillow mysqlclient django-markdownx html5lib-truncation
```

### Texte au format markdown

Avoir le texte au format markdown permet de stocker que le texte (et les images) dans la BD
et d’avoir tout de même un rendu html plus sympa. Tout est déjà fait par le package 
django-markdownx et il suffit de le régler.

Nous utiliserons toutefois les extensions disponibles de base.
Les extensions activées dans le projet :
* extra 
    * abbr (abréviations)
    * attr_list (liste d’attributs)
    * def_list (liste de définitions)
    * fenced_code (permet l’insertion de blocs de code)
    * footnotes (note de bas de page)
    * md_in_html (lit le markdown qui est dans du html)
    * tables (tableaux)
* codehilite (mise en couleur des blocs de code)

Toute la doc est [là](https://neutronx.github.io/django-markdownx/), 
ainsi que la documentation de l’implémentation python de markdown [là](https://python-markdown.github.io/).

### User avec profil

Il semble que django ait déjà prévu ce cas d’utilisation. Il semble que la meilleure façon de procéder
soit de créer un profil avec une relation `OneToOne` avec un utilisateur plutôt que de créer un 
`User` personnalisé.

```python
"""Fichier UserProfile.models.py pour les modèles d’utilisateurs"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Exemple de profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    avatar = models.ImageField(blank=True, null=True, verbose_name="avatar")
    birthDate = models.DateField(blank=True, null=True, verbose_name="date de naissance")


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Lorsque l’on crée un `User`, cela crée un profil aussi."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Lorsque l’on sauve un `User` on le fait aussi pour son profil."""
    instance.userprofile.save()
```

Pour Ajouter dans les page d’administration, il suffit de supprimer du registre l’utilisateur.

```python
"""admin.py exemple de profile user"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from multisite.connector.models import UserProfile


class UserProfileInline(admin.StackedInline):
    """definition d'un descripteur inline pour le model profil"""
    model = UserProfile
    can_delete = False
    verbose_name = 'Utilisateur'
    verbose_name_plural = 'Utilisateurs'


class UserAdmin(BaseUserAdmin):
    """définition d'un nouveau User Admin"""
    inlines = (UserProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
```

En plus de cela, des formulaires ont été crées afin d’accéder et modifier les différents champs.

Cette implémentation est mise dans une app à part, afin d'être disponible (et commune) à toutes les autres apps.

### Distribution de plusieurs sites

La distribution de plusieurs sites est possible avec django en utilisant un middleware.

Nous utiliserons celui-ci :

```python
"""Creation d’un middleware pour la gestion des hôtes virtuels"""
virtual_hosts = {
    "www.argawaen.net": "www.urls",
    "127.0.0.1": "multisite.urls"
}


class VHostMiddleware:
    """Classe de gestion des hôtes virtuels"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # On cherche à connaitre quel seront les urls racines.
        host = request.get_host()
        request.urlconf = virtual_hosts.get(host)
        # Attention à l’ordre.
        response = self.get_response(request)
        return response
```

Il faut également configurer les settings pour être capable de servir ces noms de domaines, 
ainsi que d’appeler le middleware de redirection.
