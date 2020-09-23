"""
definition of a sensor
"""
import datetime
import pytz
from .models import MeteoValue

class tlimit:

    def __init__(self, name, text):
        self.name = name
        self.text = text


time_limit = [
    tlimit("All", "All Data"),
    tlimit("day", "Current day"),
    tlimit("24hours", "Last 24 hours"),
    tlimit("3days", "Three last days"),
    tlimit("7days", "Seven last days"),
    tlimit("month", "Current month"),
    tlimit("30days", "Last 30 days"),
    tlimit("year", "Current year"),
]

tz = pytz.timezone("Europe/Paris")
utz = pytz.timezone("UTC")


def get_data(last):
    """
    get the database data on the last period
    :param last: duration of the  period
    :return: the data
    """
    if last == "All":
        return MeteoValue.objects.all()
    limit = datetime.datetime.now().astimezone(utz)
    if last == "24hours":
        limit -= datetime.timedelta(hours=24)
    else:
        limit = limit.replace(hour=0, minute=0, second=0, microsecond=0)

    if last == "3days":
        limit -= datetime.timedelta(days=3)
    elif last == "7days":
        limit -= datetime.timedelta(days=7)
    elif last == "month":
        limit = limit.replace(day=1)
    elif last == "30days":
        limit -= datetime.timedelta(days=30)
    elif last == "year":
        limit = limit.replace(day=1, month=1)
    val = MeteoValue.objects.filter(date__gte=limit)
    if len(val) == 0:
        val = MeteoValue.objects.all()
    return val


def smooth_data(data, smooth_width):
    """
    smooth the curve plotted by data
    :param data: the input data
    :param smooth_width: the width of the mobile average
    :return: the smoothed data
    """
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


def resample_data(data, entity_number):
    """
    limit the amount of dat
    :param data: input data
    :param entity_number: maximum number of entity in output
    :return: he resampled data
    """
    if len(data) <= entity_number:
        # not that many entity: nothing to do
        return data
    interval = int(len(data)/entity_number + 1)
    out = []
    for i, dat in enumerate(data):
        if i % interval == 0:
            out.append(dat)
    return out


class displaydata:
    """
    lass to encapsulate the meteo result to display
    """
    def __init__(self):
        self.temperature = "0"
        self.temp_tendance = ""
        self.temp_max = "0"
        self.temp_min = "0"
        self.temp_max_date = "0"
        self.temp_min_date = "0"
        self.temp_mean = "0"
        self.humidity = "0"
        self.hum_tendance = ""
        self.hum_max = "0"
        self.hum_min = "0"
        self.hum_max_date = "0"
        self.hum_min_date = "0"
        self.hum_mean = "0"

    def __tendance(self, dt, seuil):
        if len(dt) < 3:
            return "mdi-arrow-left-right-bold-outline tgreen"
        if len(dt) > 20:
            p1 = dt[-20]
            p2 = dt[-10]
            p3 = dt[-1]
        else:
            p1 = dt[0]
            p2 = dt[len(dt)/2]
            p3 = dt[-1]
        if abs(p3 - p2) < seuil:
            return "mdi-arrow-left-right-bold-outline tgreen"
        elif (abs(p2 - p1) < seuil and p3 > p2) or (abs(p3 - p2) < seuil and p2 > p1):
            return "mdi-arrow-top-right-bold-outline torange"
        elif (abs(p2 - p1) < seuil and p3 < p2) or (abs(p3 - p2) < seuil and p2 < p1):
            return "mdi-arrow-bottom-right-bold-outline tlightblue"
        elif p1 > p2 > p3:
            return "mdi-arrow-bottom-right-bold-outline tlightblue"
        elif p1 < p2 < p3:
            return "mdi-arrow-up-bold-outline tred"
        else:
            return "mdi-arrow-left-right-bold-outline tgreen"

    def compute_from_data(self, dta, dha, date):
        self.temp_max = -2000
        self.temp_min = 2000
        self.temp_mean = 0
        for i, t in enumerate(dta):
            self.temp_mean += t
            if t > self.temp_max:
                self.temp_max = t
                self.temp_max_date = date[i]
            if t < self.temp_min:
                self.temp_min = t
                self.temp_min_date = date[i]
        if len(dta) > 0:
            self.temp_mean = "{:.2f}".format(self.temp_mean / float(len(dta)))
        self.temp_max = "{:.2f}".format(self.temp_max)
        self.temp_min = "{:.2f}".format(self.temp_min)
        self.temperature = "{:.2f}".format(dta[-1])
        self.temp_tendance = self.__tendance(dta, 0.05)

        self.hum_max = -2000
        self.hum_min = 2000
        self.hum_mean = 0
        for i, t in enumerate(dha):
            self.hum_mean += t
            if t > self.hum_max:
                self.hum_max = t
                self.hum_max_date = date[i]
            if t < self.hum_min:
                self.hum_min = t
                self.hum_min_date = date[i]
        if len(dha) > 0:
            self.hum_mean = "{:.2f}".format(self.hum_mean / float(len(dha)))
        self.hum_max = "{:.2f}".format(self.hum_max)
        self.hum_min = "{:.2f}".format(self.hum_min)
        self.hum_tendance = self.__tendance(dha, 0.05)
        self.humidity = "{:.2f}".format(dha[-1])


def getData(ll, smoo):
    data = resample_data(get_data(ll), 1000)
    if smoo > 0:
        data = smooth_data(data, smoo)
    print(len(data))
    dates = []
    temperatures = []
    humidity = []
    i = 0
    for sset in data:
        i += 1
        dates.append(sset.date.strftime("%Y-%m-%d %H:%M:%S"))
        temperatures.append(sset.server_room_temperature)
        humidity.append(sset.server_room_humidity)
    d = displaydata()
    d.compute_from_data(temperatures, humidity, dates)
    return dates, temperatures, humidity, d
