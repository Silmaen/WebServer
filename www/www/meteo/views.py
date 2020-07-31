"""meteo.views"""
from django.shortcuts import render
from .models import MeteoValue
import pytz, datetime

tz = pytz.timezone("Europe/Paris")


def get_data(last):
    """
    get the database data on the last period
    :param last: duration of the  period
    """
    if last == "All":
        return MeteoValue.objects.all()
    limit = datetime.datetime.now().astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    if last == "3days":
        limit -= datetime.timedelta(days=3)
    if last == "week":
        limit -= datetime.timedelta(weeks=1)
    if last == "month":
        limit = limit.replace(day=1)
    if last == "year":
        limit = limit.replace(day=1, month=1)
    return MeteoValue.objects.filter(date__gte=limit)


def smooth_data(data, smooth_width):
    out = []
    for i, dat in enumerate(data):
        low = max(0, i - smooth_width)
        high = min((len(data) - 1), low + 2 * smooth_width)
        n = 0
        s_temperature = 0
        s_humidity = 0
        for d in data[low:high]:
            n += 1
            s_temperature += d.server_room_temperature
            s_humidity += d.server_room_humidity
        s_temperature /= float(max(1, n))
        s_humidity /= float(max(1, n))
        out.append(MeteoValue(date=dat.date, server_room_temperature=s_temperature, server_room_humidity=s_humidity))
    return out


class displaydata:
    def __init__(self, t=0, tt="", h=0, ht=""):
        self.temperature = str(t)
        self.temp_tendance = tt
        self.humidity = str(h)
        self.hum_tendance = ht

    def compute_from_data(self, dta, dha):
        ma = max(dta)
        mi = min(dta)
        if abs(mi - dta[0]) < 0.2 and abs(ma - dta[-1]) < 0.2:
            self.temp_tendance = "mdi-arrow-up-bold-outline tred"
        elif abs(ma - dta[0]) < 0.2 and abs(mi - dta[-1]) < 0.2:
            self.temp_tendance = "mdi-arrow-down-bold-outline tblue"
        elif dta[0] > dta[-1]:
            self.temp_tendance = "mdi-arrow-top-right-bold-outline torange"
        elif dta[-1] > dta[0]:
            self.temp_tendance = "mdi-arrow-bottom-right-outline tlightblue"
        else:
            self.temp_tendance = "mdi-arrow-left-right-outline tgreen"
        self.temperature = "{:.2f}".format(dta[-1])
        ma = max(dha)
        mi = min(dha)
        if abs(mi - dha[0]) < 0.2 and abs(ma - dha[-1]) < 0.2:
            self.hum_tendance = "mdi-arrow-up-bold-outline tred"
        elif abs(ma - dha[0]) < 0.2 and abs(mi - dha[-1]) < 0.2:
            self.hum_tendance = "mdi-arrow-down-bold-outline tblue"
        elif dta[0] > dha[-1]:
            self.hum_tendance = "mdi-arrow-top-right-bold-outline torange"
        elif dta[-1] > dha[0]:
            self.hum_tendance = "mdi-arrow-bottom-right-outline tlightblue"
        else:
            self.hum_tendance = "mdi-arrow-left-right-outline tgreen"
        self.humidity = "{:.2f}".format(dha[-1])


def index(request):
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
            print(ll)
            if not ll:
                ll = "All"
        except:
            ll = "All"
    if smoo > 0:
        data = smooth_data(get_data(ll), smoo)
    else:
        data = get_data(ll)
    dates = []
    temperatures = []
    humidity = []
    i = 0
    for sset in data:
        i += 1
        dates.append(str(sset.date))
        temperatures.append(sset.server_room_temperature)
        humidity.append(sset.server_room_humidity)
    d = displaydata()
    if len(temperatures)> 20:
        d.compute_from_data(temperatures[-20:], humidity[-20:])
    else:
        d.compute_from_data(temperatures, humidity)
    return render(request, "baseMeteo.html",
                  {'dates'       : dates,
                   'temperatures': temperatures,
                   'humidity'    : humidity,
                   'smoothing'   : smoo,
                   'last'        : ll,
                   'current'     : d,
                   })
