"""main.models"""
from django.db import models
from django.utils import timezone


# Create your models here.
class DroneConfiguration(models):
    """
    class for describing drone configuration
    """
    version_number = models.CharField(max_length=10)
    nick_name = models.CharField(max_length=40, null=True)
    components = models.TextField(null=True)
    improvement_summary = models.TextField(null=True)
    comments = models.TextField(null=True)
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de realisation")

    class Meta:
        """
        Meta data for drone
        """
        verbose_name = "Configuration Drone"
        ordering = ['date']

    def __str__(self):
        if self.nick_name not in [None, ""]:
            return "Version " + str(self.version_number) + " " + str(self.nick_name)
        return "Version " + str(self.version_number)


class DroneFlight(models):
    """
    class handling drone flights
    """
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de realisation")
    name = models.CharField(max_length=40, null=True)
    meteo = models.TextField(null=True)
    summary = models.TextField()
    comments = models.TextField()
    drone_configuration = models.ForeignKey('DroneConfiguration', on_delete=models.CASCADE)

    class Meta:
        """
        Meta data for drone
        """
        verbose_name = "Vol de  Drone"
        ordering = ['date']

    def __str__(self):
        if self.name not in [None, ""]:
            return str(self.name) + " du " + str(self.date)
        return "Vol du " + str(self.date)
