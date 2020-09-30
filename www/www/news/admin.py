"""news.admin"""
from django.contrib import admin
from django.utils.text import Truncator

from .models import Categorie, SousCategorie, Article, ExtPage, WebPage, subWebPage


class ArticleAdmin(admin.ModelAdmin):
    """
    Admin page for articles
    """
    list_display = (
        'needuser', 'ishidden', 'categorie', 'sous_categorie', 'titre', 'auteur', 'date', 'content_overview')
    list_filter = ('auteur', 'categorie', 'sous_categorie',)
    date_hierarchy = 'date'
    ordering = ('categorie', 'date', 'sous_categorie',)
    search_fields = ('titre', 'contenu')
    prepopulated_fields = {'slug': ('titre',), }
    # Configuration du formulaire d'édition
    fieldsets = (
        # Fieldset 1 : meta-info (titre, auteur…)
        ('General', {
            'fields': ('titre', 'slug', 'auteur', 'categorie', 'sous_categorie'),
        }),
        # Fieldset 2 : acces
        ('Acces', {
            'fields': ('needuser', 'ishidden',)
        }),
        # Fieldset 3 : contenu de l'article
        ('Content of the article', {
            'description': 'Content must be written in HTML format. ',
            'fields': ('contenu',)
        }),
    )

    def content_overview(self, article):
        """ 
        Returns the 40 first characters of the article's content,
        followed by '...' is text is longer.
        """
        return Truncator(article.contenu).chars(40, truncate='...')

    content_overview.short_description = 'content overview'


admin.site.register(Categorie)
admin.site.register(SousCategorie)
admin.site.register(Article, ArticleAdmin)

admin.site.register(ExtPage)
admin.site.register(WebPage)
admin.site.register(subWebPage)
