"""meteo.views"""
from django.shortcuts import render
from .Sensor import getData, time_limit, get_actual_data
from www import settings
from www.render_utils import get_page_data

subpages = [
    {
        "name": "summary",
        "url": "summary",
        "icon": "mdi-home",
        "Active"           : True,
        "NeedUser"         : True,
        "NeedStaff"        : False,
        "NeedDev"          : False,
        "NeedValidatedUser": True,
    },
    {
        "name": "desk",
        "url": "desk",
        "icon": "mdi-desk",
        "Active"           : True,
        "NeedUser"         : True,
        "NeedStaff"        : False,
        "NeedDev"          : False,
        "NeedValidatedUser": True,
    },
    {
        "name": "station",
        "url": "station",
        "icon": "mdi-cash-register",
        "Active"           : True,
        "NeedUser"         : True,
        "NeedStaff"        : False,
        "NeedDev"          : False,
        "NeedValidatedUser": True,
    }
]


def index(request):
    return summary(request)


def summary(request):
    d = get_actual_data()
    data = get_page_data(request.user, "meteo")
    return render(request, "www/MeteoSummary.html", {
        **settings.base_info, **data,
        "subpages": subpages,
        "subpage" : "Résumé météo",
        "data": {
            'ServerRoomTemp': d[0],
            'ServerRoomHumi': d[1]
        }
    })


def desk(request):
    return renderpage(request, "Bureau")


def station(request):
    return renderpage(request, "Station")


def renderpage(request, subpage):
    data = get_page_data(request.user, "meteo")
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

    return render(request, "www/MeteoServerRoom.html", {
        **settings.base_info, **data,
        "subpages": subpages,
        "subpage"       : subpage,
        "data": {
            'dates': dates,
            'temperatures': temperatures,
            'humidity': humidity,
            'smoothing': smoo,
            'last': ll,
            'current': d,
            'time_limit': time_limit
        }
    })
