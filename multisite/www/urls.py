"""Fichier main.urls.py définissant les urls."""
from django.conf.urls.static import static
from django.conf import settings as main_settings
from django.urls import path
from .views import (
    accueil, a_propos, a_propos_cv, a_propos_publications,
    mes_projets, archives, news, news_page,
    detailed_news, research, bricolage, administration, admin_users,
)


urlpatterns = [
    path("", accueil, name='accueil'),
    path('a-propos/', a_propos, name='a_propos'),
    path('a-propos/cv/', a_propos_cv, name='a_propos_cv'),
    path('a-propos/publications/', a_propos_publications, name='a_propos_publications'),
    path('mes-projets/', mes_projets, name='mes_projets'),
    path('archives/', archives, name='archives'),
    path('archives/news/', news, name='archives_news'),
    path('archives/news/<int:n_page>', news_page, name='archives_news_page'),
    path('archives/article/<int:article_id>', detailed_news, name='detailed_news'),
    path('archives/research/', research, name='archives_research'),
    path('bricolage/', bricolage, name='bricolage'),
    path('administration/', administration, name='administration'),
    path('administration/utilisateurs/', admin_users, name='admin_users'),
] + static(main_settings.MEDIA_URL, document_root=main_settings.MEDIA_ROOT)
