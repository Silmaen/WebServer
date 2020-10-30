"""main.admin"""
from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin
from django.utils.text import Truncator
from .models import *


# Register your models here.
class ArticleAdmin(MarkdownxModelAdmin):
    """
    Admin page for articles
    """
    list_display = ('titre', 'auteur', 'date', 'content_overview')
    list_filter = ('auteur', 'date')
    date_hierarchy = 'date'
    ordering = ('date', 'auteur',)
    search_fields = ('titre', 'contenu')
    prepopulated_fields = {'slug': ('titre',),}
    # Configuration du formulaire d'édition
    fieldsets = (
        # Fieldset 1 : meta-info (titre, auteur…)
        ('General', {
            'fields': ('titre', 'slug', 'auteur', 'date'),
        }),
        # Fieldset 2 : contenu de l'article
        ('Content of the article', {
            'description': 'Content must be written in Markdown format. ',
            'fields': ('contenu',)
        }),
    )

    def save_form(self, request, form, change):
        obj = super(ArticleAdmin, self).save_form(request, form, change)
        if not change:
            obj.auteur = request.user
        return obj

    def content_overview(self, article):
        """
        Returns the 40 first characters of the article's content,
        followed by '...' is text is longer.
        """
        return Truncator(article.contenu).chars(40, truncate='...')

    content_overview.short_description = 'content overview'


admin.site.register(Article, ArticleAdmin)
admin.site.register(DroneComponentCategory)
admin.site.register(DroneComponent, MarkdownxModelAdmin)
admin.site.register(DroneConfiguration, MarkdownxModelAdmin)
admin.site.register(DroneFlight, MarkdownxModelAdmin)
