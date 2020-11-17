"""Les modèles pour test subjects"""
from django.db import models
from common.models import SiteArticle

class tsjtCategorie(models.Model):
    nom = models.CharField(max_length=30)

    def __str__(self):
        return self.nom


class tsjtArticle(SiteArticle):
    categorie = models.ForeignKey(tsjtCategorie, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="tsjt/ArticleImages/", blank=True)

