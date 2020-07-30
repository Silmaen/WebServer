"""meteo.views"""
from django.shortcuts import render
from .models import MeteoValue
import pytz
tz = pytz.timezone("Europe/Paris")


def index(request):
    data = MeteoValue.objects.all()
    dates = []
    temperatures = []
    humidity = []
    i = 0
    for sset in data:
        i += 1
        dates.append(str(sset.date.astimezone(tz)))
        temperatures.append(sset.server_room_temperature)
        humidity.append(sset.server_room_humidity)
    return render(request, "baseMeteo.html", {'dates': dates, 'temperatures': temperatures, 'humidity': humidity})
