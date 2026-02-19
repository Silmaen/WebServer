"""multisite URL Configuration"""
from django.contrib import admin
from django.urls import path, include

from www.urls import urlpatterns as www_patterns

urlpatterns = www_patterns + [
    path('profile/', include('connector.urls')),
    path('admin/', admin.site.urls),
    path('markdownx/', include('markdownx.urls')),
]
