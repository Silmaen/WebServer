from django.contrib import admin
from django.utils.text import Truncator
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from news.models import Categorie, SousCategorie, Article#, CustomUser
#from news.forms import CustomUserCreationForm, CustomUserChangeForm

#class CustomUserAdmin(UserAdmin):
#    add_form = CustomUserCreationForm
#    form = CustomUserChangeForm
#    model = CustomUser
#    list_display = ['email', 'username',]

class ArticleAdmin(admin.ModelAdmin):
    list_display   = ('categorie','sous_categorie', 'titre', 'auteur', 'date', 'apercu_contenu')
    list_filter    = ('auteur', 'categorie', 'sous_categorie',)
    date_hierarchy = 'date'
    ordering       = ('categorie', 'date', 'sous_categorie',)
    search_fields  = ('titre', 'contenu')
    prepopulated_fields = {'slug': ('titre', ), }
    # Configuration du formulaire d'édition
    fieldsets = (
        # Fieldset 1 : meta-info (titre, auteur…)
       ('Général', {
            'classes': ['collapse', ],
            'fields': ('titre', 'slug', 'auteur', 'categorie', 'sous_categorie'),
        }),
        # Fieldset 2 : contenu de l'article
        ('Contenu de l\'article', {
           'description': 'Le formulaire accepte les balises HTML. Utilisez-les à bon escient !',
           'fields': ('contenu', 'image' )
        }),
    )

    def apercu_contenu(self, article):
        """ 
        Retourne les 40 premiers caractères du contenu de l'article, 
        suivi de points de suspension si le texte est plus long. 
        """
        return Truncator(article.contenu).chars(40, truncate='...')

    apercu_contenu.short_description = 'Aperçu du contenu'

#admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Categorie)
admin.site.register(SousCategorie)
admin.site.register(Article,ArticleAdmin)
