"""meteo.admin"""
from django.contrib import admin
from .models import MeteoValue

MeteoValue.objects
# Register your models here.
admin.site.register(MeteoValue)
