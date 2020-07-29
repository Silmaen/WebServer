"""meteo.models"""
from django.db import models
from django.utils import timezone


# Create your models here.
class MeteoValue(models.Model):
    """
    model for meteo value
    """
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de mesure")
    server_room_temperature = models.FloatField(default=0.0)
    server_room_humidity = models.FloatField(default=0.0)

    def __str__(self):
        return str(self.date) + " " + str(self.server_room_temperature) + " " + str(self.server_room_humidity)
