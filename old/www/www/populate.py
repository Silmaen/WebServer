from meteo.models import MeteoValue
import datetime
import pytz
tz = pytz.timezone("Europe/Paris")


def check():
	data = MeteoValue.objects.all()
	i = 0
	for sset in data:
		i += 1
		print(str(type(sset.date)) + " " + str(sset.date) + " " + str(sset.date.astimezone(tz)))
		if i > 10:
			break


def pop():
	MeteoValue.objects.all().delete()
	f = open("data.log")
	lines = f.readlines()
	f.close()
	i = 0
	start = 0
	for line in lines:
		i += 1
		line = line.strip()
		if len(line) == 0:
			continue
		if line.startswith("date"):
			continue
		if line.startswith("id"):
			start = 1
			continue
		items = line.split()
		datentime = items[start] + " " + items[start + 1]
		dt = datetime.datetime.strptime(datentime, "%Y-%m-%d %H:%M:%S")
		dtt = dt.astimezone(tz)
		m = MeteoValue(date=dtt, server_room_temperature=float(items[start + 2]), server_room_humidity=float(items[start + 3]))
		m.save()
		#if i >= 100:
		#	break


if __name__ == "__main__":
	pop()
