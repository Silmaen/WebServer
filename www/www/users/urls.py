"""users.urls"""
from django.urls import path

from . import views as userviews

urlpatterns = [
    path('signup/', userviews.SignUpView.as_view(), name='signup'),
    path('compte/', userviews.UserSettings.as_view(), name='compte'),
]
