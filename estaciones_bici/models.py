from django.db import models
from api_punts_carrega.models import Usuario
from django.utils.timezone import now, timedelta


# ---------------- ENUMS ---------------- #



# ---------------- MODELOS ---------------- #

class EstacionBici(models.Model):
    station_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    post_code = models.CharField(max_length=10, null=True, blank=True)
    lat = models.FloatField()
    lon = models.FloatField()
    capacity = models.IntegerField()
    is_charging_station = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.station_id})"

class DisponibilidadEstacionBici(models.Model):
    estacion = models.OneToOneField(EstacionBici, on_delete=models.CASCADE, related_name='estado')
    num_bicis_disponibles = models.IntegerField(default=0)
    num_bicis_mecanicas = models.IntegerField(default=0)
    num_bicis_electricas = models.IntegerField(default=0)
    num_docks_disponibles = models.IntegerField(default=0)
    estado = models.CharField(max_length=50, default="IN_SERVICE")

    def __str__(self):
        return f"Estado de {self.estacion}"

class UltimaActualizacionBicing(models.Model):
    tipo = models.CharField(max_length=50, unique=True)  # ej: 'disponibilidad', 'informacion'
    fecha_llamada = models.DateTimeField()               # cuándo hiciste la llamada tú
    fecha_actualizacion_api = models.DateTimeField()     # qué fecha marcó la API

    def __str__(self):
        return f"{self.tipo}: llamada={self.fecha_llamada}, api={self.fecha_actualizacion_api}"
    
class ReservaBici(models.Model):
    TIPOS = (
        ('mecanica', 'Mecánica'),
        ('electrica', 'Eléctrica'),
    )

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    estacion = models.ForeignKey(EstacionBici, on_delete=models.CASCADE)
    tipo_bicicleta = models.CharField(max_length=20, choices=TIPOS)
    creada_en = models.DateTimeField(auto_now_add=True)
    expiracion = models.DateTimeField()
    activa = models.BooleanField(default=True)

    def ha_expirado(self) -> bool:
        return now() > self.expiracion

    def __str__(self):
        return f"{self.usuario} - {self.tipo_bicicleta} en {self.estacion} hasta {self.expiracion}"