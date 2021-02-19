"""Configuration de l'administration"""
from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin

from .models import *


# Register your models here.
class PlantTypeAdmin(admin.ModelAdmin):
    """
    Admin page for plant type
    """
    list_display = ('name', 'vendeur',)
    list_filter = ('name', 'vendeur',)
    ordering = ('name',)
    search_fields = ('name', 'vendeur',)
    # Configuration du formulaire d’édition
    fieldsets = (
        # Fieldset 1 : meta-info (titre, auteur…)
        ('General', {
            'fields': ('name', 'vendeur', 'icon', 'stock_status'),
        }),
        # Fieldset 3 : contenu de l'article
        ('Description', {
            'fields': ('specifications', 'description',)
        }),
    )


class PlantTypeCommentAdmin(MarkdownxModelAdmin):
    list_display = ('auteur', 'contenu', 'type_plant', 'date', 'active')
    list_filter = ('auteur', 'date', 'active')
    ordering = ('type_plant', '-date', 'auteur',)
    search_fields = ('auteur', 'contenu')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(active=True)

    def save_model(self, request, obj, form, change):
        obj.auteur = request.user
        super(PlantTypeCommentAdmin, self).save_model(request, obj, form, change)


class PlantationAdmin(admin.ModelAdmin):
    """
    Admin page for plant type
    """
    list_display = ('graine', 'Semis', 'SemisTerre', 'Harvested')
    list_filter = ('graine', 'Semis', 'SemisTerre', 'Harvested')
    ordering = ('graine', 'Semis',)
    search_fields = ('graine', 'Semis', 'SemisTerre', 'Harvested')
    # Configuration du formulaire d’édition
    fieldsets = (
        # Fieldset 1 : meta-info (titre, auteur…)
        ('General', {
            'fields': ('Semis', 'SemisTerre', 'Harvested'),
        }),
        # Fieldset 2 : meta-info (titre, auteur…)
        ('General', {
            'fields': ('graine', 'semis_status', 'Coordinates',),
        }),
        # Fieldset 3 : contenu de l'article
        ('Description', {
            'fields': ('Commentaires',)
        }),
    )


class PlantationCommentAdmin(MarkdownxModelAdmin):
    list_display = ('auteur', 'contenu', 'plantation', 'date', 'active')
    list_filter = ('auteur', 'date', 'active')
    ordering = ('plantation', '-date', 'auteur',)
    search_fields = ('auteur', 'contenu')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(active=True)

    def save_model(self, request, obj, form, change):
        obj.auteur = request.user
        super(PlantationCommentAdmin, self).save_model(request, obj, form, change)


admin.site.register(PlantType, PlantTypeAdmin)
admin.site.register(PlantTypeComment, PlantTypeCommentAdmin)
admin.site.register(Plantation, PlantationAdmin)
admin.site.register(PlantationComment, PlantationCommentAdmin)
