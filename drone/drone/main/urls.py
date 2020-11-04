"""main.urls"""
from django.urls import path
from django.conf.urls import include, url
from django.contrib.auth import views as passvw
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('news', views.index, name='news'),
    path('news/<int:article_id>', views.detailed_article, name='detailed_article'),
    path('vols', views.vols, name='vols'),
    path('vols/<int:vol_id>', views.detailed_vol, name='detailed_vols'),
    path('confs', views.configurations, name='confs'),
    path('confs/<int:conf_id>', views.detailed_configuration, name='detailed_confs'),
    path('comps', views.composants, name='comps'),
    path('comps/<int:comp_id>', views.detailed_composant, name='detailed_comps'),
    url(r"^accounts/", include("django.contrib.auth.urls")),
    url(r"^register/", views.register, name="register"),
    url(r"^profile/$", views.profile, name="profile"),
    url(r"^profile/edit/", views.profile_edit, name="profile_edit"),
    url(r"^profile/password/", passvw.PasswordChangeView.as_view() , name="password"),
]
