"""
definition of a sensor
"""
import datetime
import pytz

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


def request_meteodata(request: str):
    """
    execute a request in the MeteoData database
    :param request: the request to execute
    :return: the feteched result
    """
    import MySQLdb
    MySQLParams = {
        'host'  : "localhost",
        'user'  : "MeteoRobot",
        'passwd': "robot",
        'db'    : "MeteoData"
    }
    try:
        con = MySQLdb.connect(**MySQLParams)
        cur = con.cursor()
        cur.execute(request)
        con.commit()
        data = cur.fetchall()
    except MySQLdb.Error as err:
        print(str(err))
        return []
    except Exception as err:
        print(str(err))
        return []
    con.close()
    return data


class SensorData:
    date = datetime.datetime(1970, 1, 1, 0, 0, 0)
    server_room_temperature = 0.0
    server_room_humidity = 0.0

    def __init__(self, d, t, h):
        self.date = d
        self.server_room_temperature = t
        self.server_room_humidity = h

    def __str__(self):
        return str(self.date) + " {:.2f}°C {:.1f}%".format(self.server_room_temperature, self.server_room_humidity)


def get_data(last):
    """
    get the database data on the last period
    :param last: duration of the  period
    :return: the data
    """
    import MySQLdb
    MySQLParams = {
        'host'  : "localhost",
        'user'  : "MeteoRobot",
        'passwd': "robot",
        'db'    : "MeteoData"
    }
    Table = "ServerRoom"
    filter = ""
    if last == "lastone":
        data = request_meteodata("SELECT * from `ServerRoom` ORDER BY id DESC LIMIT 1 ")
        if (len(data) == 0):
            return [SensorData(datetime.datetime.now(), 0, 0)]
        res = []
        for d in data:
            res.append(SensorData(d[1], d[2], d[3]))
        return res
    if last != "All":
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
        filter = " WHERE `date` > '" + str(limit) + "'"
    order = " ORDER BY `date` ASC"
    req = "SELECT * FROM `" + Table + "`" + filter + order
    data = request_meteodata(req)
    if len(data) == 0:
        print("no data: get all")
        req = "SELECT * FROM `" + Table + "`" + order
        data = request_meteodata(req)
    res = []
    for d in data:
        res.append(SensorData(d[1], d[2], d[3]))
    return res


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
        out.append(SensorData(dat.date, s_temperature, s_humidity))
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
        dlas = get_data("lastone")
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
        self.temperature = "{:.2f}".format(dlas[1])
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
        self.humidity = "{:.2f}".format(dlas[2])


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


def get_actual_data():
    data = get_data("lastone")
    return data[0].server_room_temperature, data[0].server_room_humidity
