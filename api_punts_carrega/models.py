from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.conf import settings



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
    CATALA = "Català"
    CASTELLANO = "Castellano"
    ENGLISH = "English"


# ---------------- MODELOS ---------------- #

class Usuario(AbstractUser):
    dni = models.CharField(max_length=20, unique=True)
    idioma = models.CharField(max_length=20, choices=Idiomas.choices, default=Idiomas.CATALA)
    telefon = models.CharField(max_length=15, blank=True, null=True)
    #foto = models.ImageField(upload_to='fotos/', blank=True, null=True)
    descripcio = models.TextField(blank=True, null=True)

    # Forzamos que el email sea único y lo usamos para login
    email = models.EmailField(unique=True)

    #valorar si permitir iniciar sesion con email y/o username, mas trabajo
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    is_admin = models.BooleanField(default=False)  # Campo para distinguir administradores

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

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
    nplaces = models.PositiveIntegerField(default=1, help_text="Número de vehículos que pueden cargar simultáneamente")
    potencia = models.IntegerField(null=True)
    tipus_velocitat = models.CharField(max_length=100, choices=Velocitat_de_carrega.choices, null=True)
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
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas')
    estacion = models.ForeignKey('EstacioCarrega', on_delete=models.CASCADE, related_name='reservas')
    hora_inicio = models.DateTimeField()
    hora_fin = models.DateTimeField()
    google_calendar_event_id = models.CharField(max_length=255, null=True, blank=True, editable=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['hora_inicio']

    def __str__(self):
        return f"Reserva en {self.estacion} el {self.fecha} a las {self.hora} por {self.duracion}"

    @property
    def duracion(self):
        if self.hora_fin and self.hora_inicio and self.hora_fin > self.hora_inicio:
            return self.hora_fin - self.hora_inicio
        return None

    def clean(self):
        if self.hora_inicio and self.hora_fin:
            if self.hora_fin <= self.hora_inicio:
                raise ValidationError("La hora de fin debe ser posterior a la hora de inicio.")
            calculated_duration = self.hora_fin - self.hora_inicio
            min_duration = timedelta(minutes=15)
            max_duration = timedelta(hours=24)
            if not (min_duration <= calculated_duration <= max_duration):
                raise ValidationError(f"La duración de la reserva ({calculated_duration}) debe estar entre {min_duration} y {max_duration}.")

        if self.estacion_id and self.hora_inicio and self.hora_fin:
            try:
                solapamientos = Reserva.objects.filter(
                    estacion_id=self.estacion_id,
                    hora_inicio__lt=self.hora_fin,
                    hora_fin__gt=self.hora_inicio
                )
                if self.pk:
                    solapamientos = solapamientos.exclude(pk=self.pk)

                n_places_disponibles = EstacioCarrega.objects.get(pk=self.estacion_id).nplaces
                if solapamientos.count() >= n_places_disponibles:
                    raise ValidationError(f"Conflicto: No hay plazas ({solapamientos.count()}/{n_places_disponibles}) en '{self.estacion_id}' para este horario.")
            except EstacioCarrega.DoesNotExist:
                raise ValidationError("La estación especificada no existe.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

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

class Valoracio(models.Model):
    reserva = models.OneToOneField(ReservaFinalitzada, on_delete=models.CASCADE, related_name="valoracio")
    puntuat = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Valoració entre 1 i 5"
    )
    ressenya = models.TextField()

    def __str__(self):
        return f"Valoració {self.puntuat}/5"

#quiza deberia heredar de Punt (debatible)
class PuntEmergencia(models.Model):
    id_emergencia = models.CharField(max_length=20, primary_key=True)
    titol = models.CharField(max_length=100)
    descripcio = models.TextField()
    actiu = models.BooleanField(default=True)
    lat = models.FloatField(null=False)
    lng = models.FloatField(null=False)

    def __str__(self):
        return f"Emergència: {self.titol}"

#no tengo claro que lo vayamos a implementar con esto el chat
class Missatge(models.Model):
    id_missatge = models.CharField(max_length=20, primary_key=True)
    missatge = models.TextField()
    data = models.DateField()
    llegit = models.BooleanField(default=False)
    usuari = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="missatges")
    punt_emergencia = models.ForeignKey(PuntEmergencia, on_delete=models.CASCADE, related_name="missatges")

    def __str__(self):
        return f"Missatge de {self.usuari.first_name} - {self.data}"

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