"""main.urls"""
from django.urls import path
from django.contrib.auth.views import *
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('news', index, name='news'),
    path('news/<int:article_id>', detailed_article, name='detailed_article'),
    path('vols', vols, name='vols'),
    path('vols/<int:vol_id>', detailed_vol, name='detailed_vols'),
    path('confs', configurations, name='confs'),
    path('confs/<int:conf_id>', detailed_configuration, name='detailed_confs'),
    path('comps', composants, name='comps'),
    path('comps/<int:comp_id>', detailed_composant, name='detailed_comps'),

    #  url(r"^accounts/", include("django.contrib.auth.urls")),
    path('profile/login/', LoginView.as_view(), name='login'),
    path('profile/logout/', LogoutView.as_view(), name='logout'),

    path('profile/password/', PasswordChangeView.as_view(), name="password"),
    path('profile/password/done', PasswordChangeDoneView.as_view(), name="password_change_done"),

    path('profile/password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('profile/password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('profile/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('profile/reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('profile/register/', register, name="register"),
    path('profile/', profile, name="profile"),
    path('profile/edit/', profile_edit, name="profile_edit"),
]
