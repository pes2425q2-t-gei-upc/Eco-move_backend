from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework import serializers
from datetime import timedelta, datetime, timezone
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from .models import EstacioCarrega, Punt, TipusCarregador, Reserva, Vehicle, ModelCotxe



class PuntSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Punt
        fields = '__all__'

class EstacioCarregaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstacioCarrega
        fields = '__all__'
    


class TipusCarregadorSerializer(serializers.ModelSerializer):   
    class Meta:
        model = TipusCarregador
        fields = '__all__'
    
class ModelCotxeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelCotxe
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):   
    class Meta:
        model = Vehicle
        fields = '__all__'
    
    


class NearestPuntCarregaSerializer(serializers.ModelSerializer):
    latitud = serializers.FloatField(required=True)
    longitud = serializers.FloatField(required=True)


User = get_user_model()
class EstacioSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstacioCarrega
        fields = ['id_punt', 'direccio', 'nplaces'] # Campos clave

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ReservaSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    estacion = EstacioSerializer(read_only=True)
    duracion = serializers.DurationField(read_only=True)

    # --- Formateo de Salida Personalizado ---
    fecha_salida = serializers.SerializerMethodField(read_only=True)
    hora_inicio_salida = serializers.SerializerMethodField(read_only=True)
    hora_fin_salida = serializers.SerializerMethodField(read_only=True)
    creado_en_salida = serializers.SerializerMethodField(read_only=True)
    modificado_en_salida = serializers.SerializerMethodField(read_only=True)

    # --- Campos para la ENTRADA (escritura) ---
    estacion_id = serializers.PrimaryKeyRelatedField(queryset=EstacioCarrega.objects.all(), source='estacion', write_only=True, required=True)
    fecha = serializers.DateField(write_only=True, required=True, input_formats=['%d/%m/%Y', '%Y-%m-%d'])
    hora = serializers.TimeField(write_only=True, required=True, input_formats=['%H:%M', '%H:%M:%S'])
    duracion_in = serializers.DurationField(write_only=True, required=True, validators=[MinValueValidator(timedelta(minutes=15)), MaxValueValidator(timedelta(hours=24))])

    # --- !!! CLASE META CORREGIDA !!! ---
    class Meta:
        model = Reserva
        # Lista TODOS los campos: los de salida formateados Y los de entrada write_only
        fields = [
            'id',
            'usuario',
            'estacion',
            # Campos formateados para la salida:
            'fecha_salida',
            'hora_inicio_salida',
            'hora_fin_salida',
            'duracion',
            'google_calendar_event_id',
            'creado_en_salida',
            'modificado_en_salida',
            # Campos write_only (necesarios en fields para DRF):
            'estacion_id',
            'fecha',
            'hora',
            'duracion_in',
        ]
        # Lista solo los campos que NO deben poder escribirse en la API
        read_only_fields = [
            'id', 'usuario', 'estacion', 'fecha_salida', 'hora_inicio_salida',
            'hora_fin_salida', 'duracion', 'google_calendar_event_id',
            'creado_en_salida', 'modificado_en_salida'
        ]

    # --- Métodos para formatear la salida ---
    def get_fecha_salida(self, obj):
        if obj.hora_inicio: return obj.hora_inicio.strftime('%d/%m/%Y')
        return None
    def get_hora_inicio_salida(self, obj):
        if obj.hora_inicio: return obj.hora_inicio.strftime('%H:%M')
        return None
    def get_hora_fin_salida(self, obj):
        if obj.hora_fin: return obj.hora_fin.strftime('%H:%M')
        return None
    def get_creado_en_salida(self, obj):
        if obj.creado_en: return obj.creado_en.strftime('%d/%m/%Y %H:%M:%S')
        return None
    def get_modificado_en_salida(self, obj):
        if obj.modificado_en: return obj.modificado_en.strftime('%d/%m/%Y %H:%M:%S')
        return None

    # --- Método validate (el que tenías antes, que funciona) ---
    def validate(self, data):
        fecha = data.get('fecha')
        hora_time = data.get('hora')
        duracion_td = data.get('duracion_in')
        estacion = data.get('estacion') # Obtenido via source='estacion'

        if not all([fecha, hora_time, duracion_td, estacion]):
            raise serializers.ValidationError("Faltan datos requeridos para la validación.")

        try:
            naive_datetime = datetime.combine(fecha, hora_time)
            if timezone.is_naive(naive_datetime):
                hora_inicio_dt = timezone.make_aware(naive_datetime)
            else:
                hora_inicio_dt = naive_datetime
            hora_fin_dt = hora_inicio_dt + duracion_td
        except Exception as e:
            raise serializers.ValidationError(f"Error calculando fechas/horas: {e}")

        if hora_fin_dt <= hora_inicio_dt:
            raise serializers.ValidationError({"__all__": "La hora de fin calculada debe ser posterior a la hora de inicio."})
        calculated_duration = hora_fin_dt - hora_inicio_dt
        min_d, max_d = timedelta(minutes=15), timedelta(hours=24)
        if not (min_d <= calculated_duration <= max_d):
            raise serializers.ValidationError({"duracion_in": f"La duración ({calculated_duration}) está fuera de los límites [{min_d}-{max_d}]."})

        try:
            solapamientos = Reserva.objects.filter(
                estacion=estacion,
                hora_inicio__lt=hora_fin_dt,
                hora_fin__gt=hora_inicio_dt
            )
            if self.instance and self.instance.pk:
                solapamientos = solapamientos.exclude(pk=self.instance.pk)

            n_places_disponibles = int(estacion.nplaces)
            if solapamientos.count() >= n_places_disponibles:
                raise serializers.ValidationError(
                    {"__all__": f"Conflicto: No hay plazas ({solapamientos.count()}/{n_places_disponibles}) en '{estacion.id_punt}' para este horario."}
                )
        except ValueError:
            raise serializers.ValidationError({"__all__": f"Error interno: Capacidad inválida para la estación."})
        except ObjectDoesNotExist:
            raise serializers.ValidationError({"estacion_id": "Estación no encontrada."})
        except Exception as e:
            print(f"Error validando solapamiento en serializer: {e}")
            raise serializers.ValidationError({"__all__": "Error comprobando disponibilidad."})

        # Devolver SOLO los campos que el MODELO espera
        validated_data_for_model = {
            'estacion': estacion,
            'hora_inicio': hora_inicio_dt,
            'hora_fin': hora_fin_dt,
        }
        return validated_data_for_model
