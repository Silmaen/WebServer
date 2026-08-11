"""Admin Django des modèles partagés."""
from django.contrib import admin
from django.utils.text import Truncator
from markdownx.admin import MarkdownxModelAdmin


class SiteArticleAdmin(admin.ModelAdmin):
    """Admin des articles : accès groupés dans un fieldset dédié."""

    list_display = (
        'titre', 'auteur', 'date', 'content_overview', 'private', 'staff')
    list_filter = ('auteur', 'date',)
    date_hierarchy = 'date'
    ordering = ('date',)
    search_fields = ('titre', 'contenu')
    prepopulated_fields = {'slug': ('titre',), }
    fieldsets = (
        ('General', {
            'fields': ('titre', 'slug', 'auteur', 'date'),
        }),
        ('Acces', {
            'fields': ('private', 'superprivate', 'staff', 'developper',)
        }),
        ('Content of the article', {
            'fields': ('contenu',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Attribue l'utilisateur courant comme auteur."""
        obj.auteur = request.user
        super().save_model(request, obj, form, change)

    def content_overview(self, article):
        """Retourne le début du contenu, tronqué pour la liste."""
        return Truncator(article.contenu).chars(40, truncate='...')

    content_overview.short_description = 'content overview'


class SiteArticleCommentAdmin(MarkdownxModelAdmin):
    """Admin des commentaires, avec une action d'approbation en lot."""

    list_display = ('auteur', 'contenu', 'article', 'date', 'active')
    list_filter = ('auteur', 'date', 'active')
    ordering = ('article', '-date', 'auteur',)
    search_fields = ('auteur', 'contenu')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        """Rend visibles les commentaires sélectionnés."""
        queryset.update(active=True)

    def save_model(self, request, obj, form, change):
        """Attribue l'utilisateur courant comme auteur."""
        obj.auteur = request.user
        super().save_model(request, obj, form, change)
