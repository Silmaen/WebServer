"""meteo.views"""
from .Sensor import getData, time_limit
from django.shortcuts import render


def index(request):
    return renderpage(request, "desk")


def desk(request):
    return renderpage(request, "desk")


def station(request):
    return renderpage(request, "station")

subpages = [
    {"url": "desk", "fct": desk, "name": "desk", "icon": "mdi mdi-desk"},
    {"url": "station", "fct": desk, "name": "station", "icon": "mdi mdi-cash-register"}
]


def renderpage(request, subpage):
    smoo = 0
    ll = "3days"
    if request.method == 'POST':
        try:
            smoo = int(request.POST.get("i_smoothing"))
            if not smoo:
                smoo = 0
        except:
            smoo = 0
        try:
            ll = request.POST.get("i_last")
            if not ll:
                ll = "All"
        except:
            ll = "All"
    dates, temperatures, humidity, d = getData(ll, smoo)
    return render(request, "baseMeteo.html",
                  {"page": "Meteo",
                   "subpage": subpage,
                   "subpages": subpages,
                   'dates': dates,
                   'temperatures': temperatures,
                   'humidity': humidity,
                   'smoothing': smoo,
                   'last': ll,
                   'current': d,
                   'time_limit': time_limit,
                   })
