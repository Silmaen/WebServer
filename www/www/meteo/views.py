"""meteo.views"""
from .Sensor import getData, time_limit, get_actual_data
from django.shortcuts import render
from news.render_utils import render_page

subpages = [
    {"url": "summary", "name": "summary", "icon": "mdi mdi-home"},
    {"url": "desk", "name": "desk", "icon": "mdi mdi-desk"},
    {"url": "station", "name": "station", "icon": "mdi mdi-cash-register"}
]


def index(request):
    return summary(request)


def summary(request):
    d = get_actual_data()
    return render_page(request, "Meteo", {"subpage": "Résumé météo"})
#    return render(request, "MeteoSummary.html",
#                  {"page": "Meteo",
#                   "subpage": "summary",
#                   "subpages": subpages,
#                   'ServerRoomTemp': d[0],
#                   'ServerRoomHumi': d[1],
#                   })


def desk(request):
    return renderpage(request, "desk")


def station(request):
    return renderpage(request, "station")



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
    return render(request, "MeteoServerRoom.html",
                  {"page": "Meteo",
                   "page_subtitle": "Information Météo locale",
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
