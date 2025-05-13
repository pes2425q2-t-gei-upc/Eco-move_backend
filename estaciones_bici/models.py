from django.db import models

class EstacionBici(models.Model):
    station_id = models.IntegerField(unique=True)  # ID externo
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    cross_street = models.CharField(max_length=255, null=True, blank=True)
    post_code = models.CharField(max_length=10, null=True, blank=True)
    lat = models.FloatField()
    lon = models.FloatField()
    altitude = models.FloatField(null=True, blank=True)
    capacity = models.IntegerField()
    is_charging_station = models.BooleanField()
    ride_code_support = models.BooleanField(default=False)
    nearby_distance = models.FloatField(null=True, blank=True)
    physical_configuration = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.station_id})"
