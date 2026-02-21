"""Fichier admin.py exemple de profil user"""
from django.contrib import admin

from common.admin import SiteArticleAdmin, SiteArticleCommentAdmin
from .models import Category, SubCategory, Article, ArticleComment, ProjetCategorie, Projet, BricolageArticle


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

admin.site.register(ArticleComment, SiteArticleCommentAdmin)


class ProjetCategorieAdmin(admin.ModelAdmin):
    """Admin pour les catégories de projet."""
    list_display = ("nom", "slug", "ordre")
    prepopulated_fields = {"slug": ("nom",)}


class ProjetAdmin(admin.ModelAdmin):
    """Admin pour les projets."""
    list_display = ("titre", "categorie", "actif", "visibilite", "date_creation", "ordre")
    list_filter = ("categorie", "actif", "visibilite")
    prepopulated_fields = {"slug": ("titre",)}
    fieldsets = (
        ("Général", {
            "fields": ("titre", "slug", "categorie", "date_creation", "actif", "visibilite", "ordre"),
        }),
        ("Apparence", {
            "fields": ("mdi_icon_name", "icone_image", "icone_url", "couleur", "lien_externe"),
        }),
        ("Contenu", {
            "fields": ("resume", "contenu"),
        }),
    )


admin.site.register(ProjetCategorie, ProjetCategorieAdmin)
admin.site.register(Projet, ProjetAdmin)


class BricolageArticleAdmin(admin.ModelAdmin):
    """Admin pour les articles de bricolage."""
    list_display = ("titre", "date")
    prepopulated_fields = {"slug": ("titre",)}


admin.site.register(BricolageArticle, BricolageArticleAdmin)
