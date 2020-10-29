"""main.models"""
from django.db import models
from django.utils import timezone


class Article(models.Model):
    """
    object to manipulate articles
    """
    titre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    auteur = models.CharField(max_length=42)
    contenu = models.TextField(null=True)
    date = models.DateTimeField(default=timezone.now,
                                verbose_name="Date de parution")

    class Meta:
        """
        Meta data for articles
        """
        verbose_name = "article"
        ordering = ['date']

    def __str__(self):
        return self.titre


class DroneComponentCategory(models.Model):
    """
    class to handle component types for drones
    """
    name = models.CharField(max_length=40)
    onBoard = models.BooleanField(verbose_name="Onboard component or Ground component")

    def __str__(self):
        return self.name


class DroneComponent(models.Model):
    """
    class to handle componets of drone
    """
    name = models.CharField(max_length=40)
    category = models.ForeignKey('DroneComponentCategory', on_delete=models.CASCADE)
    weight = models.FloatField(null=True)
    datasheet = models.URLField(null=True)

    def __str__(self):
        return self.name


# Create your models here.
class DroneConfiguration(models.Model):
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


class DroneFlight(models.Model):
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
