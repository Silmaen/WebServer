"""Fichier admin.py exemple de profil user"""
from django.contrib import admin
from common.admin import SiteArticleAdmin
from .models import Category, SubCategory, Article


class ArticleAdmin(SiteArticleAdmin):
    """
    Admin page for articles
    """
    list_display = SiteArticleAdmin.list_display + ('categorie', 'sous_categorie',)
    list_filter = SiteArticleAdmin.list_filter + ('categorie', 'sous_categorie',)
    ordering = ('categorie', 'date', 'sous_categorie',)
    # Configuration du formulaire d’édition
    fieldsets = (
        # Fieldset 1 : meta-info (titre, auteur…)
        ('Categorie', {
            'fields': ('categorie', 'sous_categorie'),
        }),
    ) + SiteArticleAdmin.fieldsets


admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Article, ArticleAdmin)
