"""multisite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns: path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('www', include('www.urls')),
    path('drone', include('drone.urls')),
    path('ayoaron', include('ayoaron.urls')),
    path('tsjt', include('tsjt.urls')),
    path('potager', include('potager.urls')),
    # Include for the system
    path('profile/', include('connector.urls')),
    path('admin/', admin.site.urls),
    path('markdownx/', include('markdownx.urls')),  # Pour le décodage de Markdown.
]
