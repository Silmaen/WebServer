"""Page d'admin pout tsjt."""
from django.contrib import admin
from common.admin import SiteArticleAdmin
from .models import tsjtCategorie, tsjtArticle


class tsjtArticleAdmin(SiteArticleAdmin):
    list_display = ('categorie', 'titre', 'auteur', 'date', 'content_overview')
    list_filter = SiteArticleAdmin.list_filter + ('categorie',)
    ordering = ('categorie',) + SiteArticleAdmin.ordering
    # Configuration du formulaire d'édition
    fieldsets = (
        # Fieldset 1 : meta-info (titre, auteur…)
        ('General', {
            'fields': ('categorie', 'titre', 'slug', 'auteur', 'date'),
        }),
        # Fieldset 2 : acces
        ('Acces', {
            'fields': ('private', 'superprivate', 'staff', 'developper',)
        }),
        # Fieldset 3 : contenu de l'article
        ('Content of the article', {
            'fields': ('contenu', 'image',)
        }),
    )


admin.site.register(tsjtCategorie)
admin.site.register(tsjtArticle, tsjtArticleAdmin)
