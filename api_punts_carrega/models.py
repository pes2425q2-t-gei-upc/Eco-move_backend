from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from cloudinary_storage.storage import MediaCloudinaryStorage

from ecomove_backend import settings


# ---------------- ENUMS ---------------- #

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

class Idiomas(models.TextChoices):
    CATALA = "Catala"
    CASTELLANO = "Castellano"
    ENGLISH = "English"


# ---------------- MODELOS ---------------- #

class TipusVelocitat(models.Model):
    id_velocitat = models.CharField(max_length=100, primary_key=True)
    nom_velocitat = models.CharField(max_length=100, choices=Velocitat_de_carrega.choices)
    
    def __str__(self):
        return f"{self.nom_velocitat}"

class Usuario(AbstractUser):
    idioma = models.CharField(max_length=20, choices=Idiomas.choices, default=Idiomas.CATALA)
    telefon = models.CharField(max_length=15, blank=True, null=True)
    foto = models.ImageField(upload_to='fotos/',storage=MediaCloudinaryStorage(), blank=True, null=True)
    descripcio = models.TextField(blank=True, null=True)
    _punts = models.IntegerField(default=0, db_column='punts')  # _ és per fer privat a python
    # Forzamos que el email sea único y lo usamos para login
    email = models.EmailField(unique=True)
    
    #valorar si permitir iniciar sesion con email y/o username, mas trabajo
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    is_admin = models.BooleanField(default=False)  # Campo para distinguir administradores

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def save(self, *args, **kwargs):
        # Eliminar imagen anterior si se está cambiando
        try:
            old = Usuario.objects.get(pk=self.pk)
            if old.foto and self.foto != old.foto:
                old.foto.delete(save=False)
        except Usuario.DoesNotExist:
            pass  # es un nuevo usuario

        super().save(*args, **kwargs)

    @property
    def punts(self):
        return self._punts
    
    @transaction.atomic
    def sumar_punts(self, cantidad):
        
        if not isinstance(cantidad, int) or cantidad <= 0:
            raise ValueError("La cantidad de puntos debe ser un entero positivo")
        
        # Refrescar el usuario desde la base de datos para evitar condiciones de carrera
        usuario_actual = Usuario.objects.select_for_update().get(pk=self.pk)
        usuario_actual._punts += cantidad
        usuario_actual.save(update_fields=['_punts'])
        
        # Actualizar el objeto actual
        self.refresh_from_db(fields=['_punts'])
        return self._punts
    
    @transaction.atomic
    def restar_punts(self, cantidad):
        if not isinstance(cantidad, int) or cantidad <= 0:
            raise ValueError("La cantidad de puntos debe ser un entero positivo")
        
        # Refrescar el usuario desde la base de datos para evitar condiciones de carrera
        usuario_actual = Usuario.objects.select_for_update().get(pk=self.pk)
        
        if usuario_actual._punts < cantidad:
            raise ValueError(f"El usuario solo tiene {usuario_actual._punts} puntos, no se pueden restar {cantidad}")
        
        usuario_actual._punts -= cantidad
        usuario_actual.save(update_fields=['_punts'])
        
        # Actualizar el objeto actual
        self.refresh_from_db(fields=['_punts'])
        return self._punts

class Punt(models.Model):
    id_punt = models.CharField(max_length=100, primary_key=True)
    lat = models.FloatField(null=False)
    lng = models.FloatField(null=False)
    direccio = models.CharField(max_length=255, null=True, blank=True)
    ciutat = models.CharField(max_length=100, null=True, blank=True)
    provincia = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Punto {self.id_punt} en {self.lat}, {self.lng}"
    
    class Meta:
        abstract = False

class EstacioCarrega(Punt):
    gestio = models.CharField(max_length=100)
    tipus_acces = models.CharField(max_length=100)
    nplaces = models.CharField(max_length=20, null=True)
    potencia = models.IntegerField(null=True)
    # tipus_velocitat = models.CharField(max_length=100, choices=Velocitat_de_carrega.choices, null=True)
    tipus_velocitat = models.ManyToManyField('TipusVelocitat', related_name='estacions_de_carrega')
    tipus_carregador = models.ManyToManyField('TipusCarregador', related_name='estacions_de_carrega')

    def __str__(self):
        return f"Estació {self.id_punt} - {self.lat}, {self.lng}"

class TipusCarregador(models.Model):
    id_carregador = models.CharField(max_length=100, primary_key=True)
    nom_tipus = models.CharField(max_length=100)
    tipus_connector = models.CharField(max_length=100)
    tipus_corrent = models.CharField(max_length=100, choices=Tipus_de_Corrent.choices)

    def __str__(self):
        return f"{self.nom_tipus} - {self.tipus_connector} ({self.tipus_corrent})"

class Reserva(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservas'
    )
    estacion = models.ForeignKey(EstacioCarrega, on_delete=models.CASCADE, related_name='reservas')
    fecha = models.DateField()
    hora = models.TimeField()
    duracion = models.DurationField(
        help_text="Reserva mínima 15 min, Reserva máxima 24 h",
        validators=[MinValueValidator(timedelta(minutes=15)), MaxValueValidator(timedelta(hours=24))]
    )
    vehicle = models.ForeignKey('Vehicle', on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')

    def __str__(self):
        user_info = f" de {self.usuario.username}" if hasattr(self, 'usuario') and self.usuario else ""
        return f"Reserva en {self.estacion} el {self.fecha} a las {self.hora}{user_info} por {self.duracion}"

class ReservaFinalitzada(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name="finalitzada")
    punts_obtinguts = models.IntegerField(default=0)
    preu = models.DecimalField(max_digits=6, decimal_places=2)
    #usuari = models.ForeignKey(Usuari, on_delete=models.CASCADE, related_name="reserves")

    def __str__(self):
        return f"Reserva Finalitzada: {self.reserva}"

class Vehicle(models.Model):
    matricula = models.CharField(max_length=10, primary_key=True)
    carrega_actual = models.FloatField()
    capacitat_bateria = models.FloatField()
    model_cotxe = models.ForeignKey('ModelCotxe', on_delete=models.CASCADE, related_name='vehicles')
    propietari = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='vehicles')

    def __str__(self):
        return f"Vehicle {self.model_cotxe.marca} {self.model_cotxe.model} ({self.matricula}) de {self.propietari}"

class ModelCotxe(models.Model):
    model = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    any_model = models.IntegerField()
    tipus_carregador = models.ManyToManyField(TipusCarregador, related_name='tipus_carregador')

    def __str__(self):
        return f"Model {self.marca} {self.model} ({self.any_model})"

class ValoracionEstacion(models.Model):
    estacion = models.ForeignKey(EstacioCarrega, on_delete=models.CASCADE, related_name="valoraciones")
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="valoraciones_estaciones")
    puntuacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Valoración entre 1 y 5"
    )
    comentario = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        # Un usuario solo puede valorar una vez cada estación
        unique_together = ('estacion', 'usuario')
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Valoración de {self.usuario.username} para {self.estacion.id_punt}: {self.puntuacion}/5"


class Report(models.Model):
    id_report = models.CharField(max_length=20, primary_key=True)
    reportador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="reports_emesos")
    reportat = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="reports_rebuts")
    administrador_assignat = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, related_name="reports_assignats",
        limit_choices_to={'is_admin': True}
    )
    missatge = models.TextField()
    #imatge = models.ImageField(upload_to='reports/')
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report {self.id_report} de {self.reportador} a {self.reportat}"

class RespostaReport(models.Model):
    report = models.OneToOneField(Report, on_delete=models.CASCADE, related_name="resposta")
    resolucio = models.CharField(max_length=50, choices=Resolucio.choices)
    missatge = models.TextField()
    data_resolucio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resposta a {self.report.id_report} - {self.resolucio}"

class Descomptes(models.Model):
    id_descompte = models.CharField(max_length=20, primary_key=True)
    nom = models.CharField(max_length=100)
    descripcio = models.TextField()
    #icona = models.ImageField(upload_to='icones/')
    punts_necessaris = models.IntegerField()
    usuaris = models.ManyToManyField(Usuario, through='DataDescompte', related_name="descomptes")

    def __str__(self):
        return f"Descompte: {self.nom}"

class DataDescompte(models.Model):
    usuari = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="descomptes_obtinguts")
    descompte = models.ForeignKey(Descomptes, on_delete=models.CASCADE, related_name="usuaris_obtenidors")
    data_obtencio = models.DateField()

    def __str__(self):
        return f"{self.usuari.first_name} va obtenir {self.descompte.nom}"
    
    class Meta:
        unique_together = ('usuari', 'descompte')


class RefugioClimatico(Punt):
    nombre = models.CharField(max_length=255)
    numero_calle = models.CharField(max_length=20, null=True, blank=True)
    
    def __str__(self):
        return f"Refugio {self.nombre} - {self.lat}, {self.lng}"
