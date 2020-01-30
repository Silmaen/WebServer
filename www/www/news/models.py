from django.db import models
from django.utils import timezone
#from django.contrib.auth.models import AbstractUser

#class CustomUser(AbstractUser):
#    pass
#    
#    def __str__(self):
#        return self.username

class Categorie(models.Model):
    '''
    Categorie des articles
    '''
    nom = models.CharField(max_length=30)
    def __str__(self):
        return self.nom

class SousCategorie(models.Model):
    '''
    Categorie des articles
    '''
    nom = models.CharField(max_length=30)
    image = models.ImageField(upload_to="SousCateIcons/",blank=True)
    def __str__(self):
        return self.nom

class Article(models.Model):
    titre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    auteur = models.CharField(max_length=42)
    contenu = models.TextField(null=True)
    date = models.DateTimeField(default=timezone.now, 
                                verbose_name="Date de parution")
    categorie = models.ForeignKey('Categorie', on_delete=models.CASCADE)
    sous_categorie = models.ForeignKey('SousCategorie', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="ArticleImages/",blank=True)
    
    class Meta:
        verbose_name = "article"
        ordering = ['date']
    
    def __str__(self):
        return self.titre