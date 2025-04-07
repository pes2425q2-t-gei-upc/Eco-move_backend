from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class Velocitat_de_carrega(models.TextChoices):
    LENTA = "Càrrega lenta"
    SEMI_RAPIDA = "Càrrega semi-ràpida"
    RAPIDA = "Càrrega ràpida"
    ULTRA_RAPIDA = "Càrrega ultra-ràpida"
    

class Tipus_de_Corrent(models.TextChoices):
    AC = "Corrent alterna"
    DC = "Corrent continua"

class Resolucio(models.TextChoices):
    USUARI_BLOQUEJAT = "Usuari bloquejat"
    MISSATGE_ELIMINAT = "Missatge eliminat"
    ABSOLT = "Absolt"

class Punt(models.Model):
    id_punt = models.CharField(max_length=100, primary_key=True)
    lat = models.FloatField(null= True)
    lng = models.FloatField(null= True)
    direccio = models.CharField(max_length=255,null=True,blank=True)
    ciutat = models.CharField(max_length=100,null= True,blank=True)
    provincia = models.CharField(max_length=100,null= True,blank=True)

    def __str__(self):
        return f"Punto {self.id_punt} en {self.lat}, {self.lng}"
    
    class Meta:
        abstract = False

class EstacioCarrega(Punt):
    gestio = models.CharField(max_length=100)
    tipus_acces =  models.CharField(max_length=100)
    nplaces = models.CharField(max_length=20,null=True)
    potencia = models.IntegerField(null = True)
    tipus_velocitat = models.CharField(max_length=100,choices=Velocitat_de_carrega.__members__.items(),null=True)
    tipus_carregador = models.ManyToManyField('TipusCarregador',related_name='estacions_de_carrega')
    
    def __str__(self):
        return f"Estació {self.id_punt} - {self.lat}, {self.lng}"
    
    
    
class TipusCarregador(models.Model):
    id_carregador = models.CharField(max_length=100, primary_key=True)
    nom_tipus = models.CharField(max_length=100)
    tipus_connector = models.CharField(max_length=100)
    tipus_corrent = models.CharField(max_length=100,choices=Tipus_de_Corrent.__members__.items())

    def __str__(self):
        return f"{self.nom_tipus} - {self.tipus_connector} ({self.tipus_corrent})"


class Reserva(models.Model):

    estacion = models.ForeignKey(EstacioCarrega, on_delete=models.CASCADE, related_name='reservas')
    fecha = models.DateField()
    hora = models.TimeField()
    duracion = models.DurationField()

    def __str__(self):
        return f"Reserva en {self.estacion} el {self.fecha} a las {self.hora} por {self.duracion}"
    

class Vehicle(models.Model):
    matricula = models.CharField(max_length=10, primary_key=True)
    carrega_actual = models.FloatField()
    Capacitat_bateria = models.FloatField()
    Model_cotxe = models.ForeignKey('ModelCotxe', on_delete=models.CASCADE, related_name='vehicles')
    '''propietari = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')'''
    
    def __str__(self):
        return f"Vehicle {self.marca} {self.model} ({self.matricula}) de" ''' {self.propietari}'''

class ModelCotxe(models.Model):
    model = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    any_model = models.IntegerField()
    tipus_carregador = models.ManyToManyField(TipusCarregador, related_name='tipus_carregador')


    def __str__(self):
        return f"Model {self.marca} {self.model} del {self.any_model}"
    