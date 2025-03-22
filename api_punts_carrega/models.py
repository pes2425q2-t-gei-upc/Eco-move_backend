from enum import Enum
from django.db import models
from django.contrib.auth.models import User

class Velocitat_de_carrega(Enum):
    LENTA = "Càrrega lenta"
    SEMI_RAPIDA = "Càrrega semi-ràpida"
    RAPIDA = "Càrrega ràpida"
    ULTRA_RAPIDA = "Càrrega ultra-ràpida"
    

class Tipus_de_Corrent(Enum):
    AC = "Corrent alterna"
    DC = "Corrent continua"

class Punt(models.Model):
    id_punt = models.CharField(max_length=100, primary_key=True)
    lat = models.FloatField(null= True)
    lng = models.FloatField(null= True)
    direccio = models.CharField(max_length=255,null=True)
    ciutat = models.CharField(max_length=100,null= True)
    provincia = models.CharField(max_length=100,null= True)

    def __str__(self):
        return f"Punto {self.id_punt} en {self.lat}, {self.lng}"
    
    class Meta:
        abstract = False

class EstacioCarrega(Punt):
    gestio = models.CharField(max_length=100)
    tipus_acces =  models.CharField(max_length=100)
    nplaces = models.CharField(max_length=20,null=True)
    
    def __str__(self):
        return f"Estació {self.id_punt} - {self.lat}, {self.lng}"
    

class PuntCarrega(models.Model):
    id_punt_carrega = models.CharField(max_length=100, primary_key=True)
    potencia = models.IntegerField()
    tipus_velocitat = models.CharField(max_length=100,choices=Velocitat_de_carrega.__members__.items())
    estacio = models.ForeignKey(EstacioCarrega, on_delete=models.SET_NULL, related_name='punt_carrega',null=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['estacio','id_punt_carrega'], name='unique_p_carrega')
        ] 
    
    def __str__(self):
        return f"Punt {self.id_punt_carrega} - {self.potencia}kW - {self.tipus_velocitat}"
    
    
class TipusCarregador(models.Model):
    id_carregador = models.CharField(max_length=100, primary_key=True)
    nom_tipus = models.CharField(max_length=100)
    tipus_connector = models.CharField(max_length=100)
    tipus_corrent = models.CharField(max_length=100,choices=Tipus_de_Corrent.__members__.items())
    punt_carrega = models.ManyToManyField(PuntCarrega,related_name='TipusCarregador')

    def __str__(self):
        return f"{self.nom_tipus} - {self.tipus_connector} ({self.tipus_corrent})"


class Reserva(models.Model):

    estacion = models.ForeignKey(EstacioCarrega, on_delete=models.CASCADE, related_name='reservas')
    fecha = models.DateField()
    hora = models.TimeField()
    duracion = models.DurationField()

    def __str__(self):
        return f"Reserva en {self.estacion} el {self.fecha} a las {self.hora} por {self.duracion}"
    

    