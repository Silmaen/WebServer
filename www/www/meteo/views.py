"""meteo.views"""
from django.shortcuts import render
from .models import MeteoValue

def index(request):
    data = MeteoValue.objects.all()
    dates = []
    temperatures = []
    humidity = []
    i = 0
    for sset in data:
        i += 1
        dates.append(str(sset.date))
        temperatures.append(sset.server_room_temperature)
        humidity.append(sset.server_room_humidity)
        #if i > 10:
           # break
    return render(request, "baseMeteo.html", {'dates': dates, 'temperatures': temperatures, 'humidity': humidity})
