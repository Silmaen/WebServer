"""Fichier main.urls.py définissant les urls."""
from django.conf.urls.static import static
from django.conf import settings as main_settings
from django.urls import path
from .views import (
    accueil, a_propos, a_propos_cv, a_propos_publications,
    mes_projets, mes_projets_categorie, mes_projets_detail,
    archives, news, news_page,
    detailed_news, research, bricolage,
    administration, admin_users,
    admin_projets, admin_projet_ajouter, admin_projet_modifier, admin_projet_supprimer,
    admin_projet_categorie_ajouter, admin_projet_categorie_modifier,
    admin_projet_categorie_supprimer,
)


urlpatterns = [
    path("", accueil, name='accueil'),
    path('a-propos/', a_propos, name='a_propos'),
    path('a-propos/cv/', a_propos_cv, name='a_propos_cv'),
    path('a-propos/publications/', a_propos_publications, name='a_propos_publications'),
    path('mes-projets/', mes_projets, name='mes_projets'),
    path('mes-projets/categorie/<slug:slug>/', mes_projets_categorie, name='mes_projets_categorie'),
    path('mes-projets/projet/<slug:slug>/', mes_projets_detail, name='mes_projets_detail'),
    path('archives/', archives, name='archives'),
    path('archives/news/', news, name='archives_news'),
    path('archives/news/<int:n_page>', news_page, name='archives_news_page'),
    path('archives/article/<int:article_id>', detailed_news, name='detailed_news'),
    path('archives/research/', research, name='archives_research'),
    path('bricolage/', bricolage, name='bricolage'),
    path('administration/', administration, name='administration'),
    path('administration/utilisateurs/', admin_users, name='admin_users'),
    path('administration/projets/', admin_projets, name='admin_projets'),
    path('administration/projets/ajouter/', admin_projet_ajouter, name='admin_projet_ajouter'),
    path('administration/projets/modifier/<int:projet_id>/', admin_projet_modifier, name='admin_projet_modifier'),
    path('administration/projets/supprimer/<int:projet_id>/', admin_projet_supprimer, name='admin_projet_supprimer'),
    path('administration/projets/categories/ajouter/', admin_projet_categorie_ajouter, name='admin_projet_categorie_ajouter'),
    path('administration/projets/categories/modifier/<int:categorie_id>/', admin_projet_categorie_modifier, name='admin_projet_categorie_modifier'),
    path('administration/projets/categories/supprimer/<int:categorie_id>/', admin_projet_categorie_supprimer, name='admin_projet_categorie_supprimer'),
] + static(main_settings.MEDIA_URL, document_root=main_settings.MEDIA_ROOT)
