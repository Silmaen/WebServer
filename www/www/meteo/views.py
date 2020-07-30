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
        dates.append(str(sset.date.astimezone(tz)))
        temperatures.append(sset.server_room_temperature)
        humidity.append(sset.server_room_humidity)
    return render(request, "baseMeteo.html",
                  {'dates': dates,
                   'temperatures': temperatures,
                   'humidity': humidity,
                   'smoothing': smoo,
                   'last': ll,
                   })
