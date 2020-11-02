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
    ordering = ('-date', 'auteur',)
    search_fields = ('titre', 'contenu')
    prepopulated_fields = {'slug': ('titre',)}
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

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super(ArticleAdmin, self).save_model(request, obj, form, change)

    def content_overview(self, article):
        """
        Returns the 40 first characters of the article's content,
        followed by '...' is text is longer.
        """
        return Truncator(article.contenu).chars(40, truncate='...')

    content_overview.short_description = 'content overview'


class ArticleCommentsAdmin(MarkdownxModelAdmin):
    list_display = ('user', 'contenu', 'article', 'date', 'active')
    list_filter = ('user', 'date', 'active')
    ordering = ('article', '-date', 'user',)
    search_fields = ('user', 'contenu')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(active=True)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super(ArticleCommentsAdmin, self).save_model(request, obj, form, change)

class DroneComponentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'onBoard')
    list_filter = ('name', 'onBoard')
    search_fields = ('name', 'onBoard')


class DroneComponentAdmin(MarkdownxModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('name', 'category')
    search_fields = ('name', 'category')


class DroneConfigurationAdmin(MarkdownxModelAdmin):
    list_display = ('version_number', 'nick_name', 'date', 'version_logiciel')
    list_filter = ('version_number', 'nick_name', 'date', 'version_logiciel')
    search_fields = ('version_number', 'nick_name', 'date', 'version_logiciel')


class DroneFlightAdmin(MarkdownxModelAdmin):
    list_display = ('name', 'date', 'drone_configuration')
    list_filter = ('name', 'date', 'drone_configuration')
    search_fields = ('name', 'date', 'drone_configuration')


admin.site.register(Article, ArticleAdmin)
admin.site.register(ArticleComments, ArticleCommentsAdmin)

admin.site.register(DroneComponentCategory, DroneComponentCategoryAdmin)
admin.site.register(DroneComponent, DroneComponentAdmin)
admin.site.register(DroneConfiguration, DroneConfigurationAdmin)
admin.site.register(DroneFlight, DroneFlightAdmin)
