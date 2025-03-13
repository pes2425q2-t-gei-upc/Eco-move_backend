from enum import Enum

class Velocitat_de_carrega(Enum):
    LENTA = "Càrrega lenta"
    SEMI_RAPIDA = "Càrrega semi-ràpida"
    RAPIDA = "Càrrega ràpida"
    ULTRA_RAPIDA = "Càrrega ultra-ràpida"
    

class Tipus_de_Corrent(Enum):
    AC = "Corrent alterna"
    DC = "Corrent continua"

from django.db import models


class Ubicacio(models.Model):
    id_ubicacio = models.CharField(max_length=100, primary_key=True)
    lat = models.FloatField()
    lng = models.FloatField()
    direccio = models.CharField(max_length=255)
    ciutat = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['lat', 'lng'], name='unique_lat_lng')
        ]
    def __str__(self):
        return f"{self.lat}, {self.lng}"

class Punt(models.Model):
    id_punt = models.CharField(max_length=100, primary_key=True)
    ubicacio_punt = models.OneToOneField(Ubicacio, on_delete=models.CASCADE, related_name='punt',null = True)
    
    def __str__(self):
        return f"Punto {self.id_punt} en {self.ubicacio_punt}"
    
    class Meta:
        abstract = False

class EstacioCarrega(Punt):
    
    id_estacio = models.CharField(max_length=100, unique=True)
    gestio = models.CharField(max_length=100)
    tipus_acces =  models.CharField(max_length=20)
    ubicacio_estacio = models.OneToOneField(Ubicacio, on_delete=models.CASCADE, related_name='estaciocarrega',null = True)
    
    def __str__(self):
        return f"Estació {self.id_estacio} - {self.ubicacio_estacio.direccio}"
    
    def save(self, *args, **kwargs):
        if not self.id_punt:
            self.id_punt = self.id_estacio
            self.ubicacio_estacio.save()
        super().save(*args, **kwargs)

class PuntCarrega(models.Model):  
    id_punt_carrega = models.CharField(max_length=100)
    potencia = models.IntegerField()
    tipus_velocitat = models.CharField(max_length=20,choices=Velocitat_de_carrega.__members__.items())
    estacio = models.ForeignKey(EstacioCarrega, on_delete=models.SET_NULL, related_name='punt_carrega',null=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['estacio', 'id_punt_carrega'], name='unique_p_carrega')
        ] 
    
    def __str__(self):
        return f"Punt {self.id_punt_carrega} - {self.potencia}kW - {self.tipus_velocitat}"
    
    
class TipusCarregador(models.Model):
    id_carregador = models.CharField(max_length=100, primary_key=True)
    nom_tipus = models.CharField(max_length=100)
    tipus_connector = models.CharField(max_length=100)
    tipus_corrent = models.CharField(max_length=20,choices=Tipus_de_Corrent.__members__.items())
    punt_carrega = models.ManyToManyField(PuntCarrega,related_name='TipusCarregador')

    def __str__(self):
        return f"{self.nom_tipus} - {self.tipus_connector} ({self.tipus_corrent})"
    

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