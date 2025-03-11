from django.db import models

class ChargingStation(models.Model):
    id_station = models.CharField(max_length=50, unique=True)
    description_location = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100, null=True, blank=True)
    power_kw = models.FloatField(null=True, blank=True)
    speed_type = models.CharField(max_length=50, null=True, blank=True)
    vehicle_type = models.CharField(max_length=50, null=True, blank=True)
    current_type = models.CharField(max_length=20, null=True, blank=True)
    connection_type = models.CharField(max_length=100, null=True, blank=True)
    num_spots = models.TextField(null=True, blank=True)
    access_type = models.CharField(max_length=50, null=True, blank=True)
    operator = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longtitude = models.FloatField(null=True, blank=True)
    updated_at= models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.description_location} - {self.city}"
