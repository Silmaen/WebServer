# users/urls.py
from django.urls import path
from . import views as userviews

urlpatterns = [
    #path('login/', SignInView.as_view(),name='login'),
    path('signup/', userviews.SignUpView.as_view(), name='signup'),
    path('compte/', userviews.UserSettings.as_view(), name='compte'),
]
