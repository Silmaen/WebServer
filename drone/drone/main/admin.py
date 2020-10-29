"""main.admin"""
from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Article)
admin.site.register(DroneComponentCategory)
admin.site.register(DroneComponent)
admin.site.register(DroneConfiguration)
admin.site.register(DroneFlight)
