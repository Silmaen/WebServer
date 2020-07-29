from meteo.models import MeteoValue
import datetime
import pytz
timezone = pytz.timezone("Europe/Paris")


def pop():
	MeteoValue.objects.all().delete()
	f = open("data.log")
	lines = f.readlines()
	f.close()
	i = 0
	for line in lines:
		i += 1
		line = line.strip()
		if len(line) == 0:
			continue
		if line.startswith("date"):
			continue
		items = line.split()
		datentime = items[0] + " " + items[1]
		dt = datetime.datetime.strptime(datentime, "%Y-%m-%d %H:%M:%S")
		dtt = timezone.localize(dt)
		m = MeteoValue(date=dtt, server_room_temperature=float(items[2]), server_room_humidity=float(items[3]))
		m.save()
		#if i >= 100:
		#	break


if __name__ == "__main__":
	pop()
