from datetime import datetime

from django.template.defaultfilters import date
from rest_framework import serializers
from .models import (
    EstacioCarrega,
    Punt,
    TipusCarregador,
    Reserva,
    Vehicle,
    RefugioClimatico,
    Usuario,
    ValoracionEstacion,
    TextItem,
    Idiomas,
    Trofeo,
    UsuarioTrofeo
)
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.utils.translation import get_language

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
    

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['matricula', 'carrega_actual', 'capacitat_bateria', 'model', 'marca', 'any_model', 'tipus_carregador']
        read_only_fields = ['propietari']

class NearestPuntCarregaSerializer(serializers.ModelSerializer):
    latitud = serializers.FloatField(required=True)
    longitud = serializers.FloatField(required=True)


class RefugioClimaticoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefugioClimatico
        fields = ['id_punt', 'nombre', 'lat', 'lng', 'direccio', 'numero_calle']

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id', 'first_name', 'last_name', 'email', 'username',
            'idioma', 'telefon', 'descripcio', 'is_admin', 'punts','foto','bloqueado']
        read_only_fields = ['id', 'punts']

class PerfilPublicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'idioma', 'descripcio','foto']

class FotoPerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'foto']
        read_only_fields = ['id']

class ReservaSerializer(serializers.ModelSerializer):
    fecha = serializers.DateField(format='%d/%m/%Y')
    hora = serializers.TimeField(format='%H:%M')
    estacion = serializers.PrimaryKeyRelatedField(
        queryset=EstacioCarrega.objects.all(),
        
    )
    vehicle = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        
        required=False,
        allow_null=True
    )
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Reserva
        fields = [
            'id',
            'usuario',
            'estacion',
            'fecha',
            'hora',
            'duracion',
            'vehicle',
        ]
        read_only_fields = ['id', 'usuario']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['fecha'] = instance.fecha.strftime('%d/%m/%Y')
        representation['hora'] = instance.hora.strftime('%H:%M')
        return representation



class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=Usuario.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    idioma = serializers.ChoiceField(choices=Idiomas.choices, required=False)
    telefon = serializers.RegexField(
        regex=r'^\d{9}$',
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Número de teléfono con 9 dígitos"
    )

    class Meta:
        model = Usuario
        fields = (
            'username', 'email', 'password', 'password2', 'first_name', 'last_name',
            'idioma', 'telefon', 'descripcio'
        )
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = Usuario.objects.create_user(**validated_data)
        user.set_password(password)  # create_user ya lo hace, pero por si acaso lo reaseguras
        user.save()
        return user


class ValoracionEstacionSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    fecha_creacion = serializers.DateTimeField(format="%d/%m/%Y %H:%M", read_only=True)
    fecha_actualizacion = serializers.DateTimeField(format="%d/%m/%Y %H:%M", read_only=True)

    class Meta:
        model = ValoracionEstacion
        fields = ['id', 'estacion', 'usuario', 'username', 'puntuacion', 'comentario',
                  'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']

    def get_username(self, obj):
        return obj.usuario.username

    def validate(self, data):
        # Validar que la puntuación esté entre 1 y 5
        if 'puntuacion' in data and (data['puntuacion'] < 1 or data['puntuacion'] > 5):
            raise serializers.ValidationError("La puntuación debe estar entre 1 y 5")
        return data



class EstacioCarregaConValoracionesSerializer(EstacioCarregaSerializer):
    valoraciones = ValoracionEstacionSerializer(many=True, read_only=True)
    puntuacion_media = serializers.SerializerMethodField()
    num_valoraciones = serializers.SerializerMethodField()

    class Meta:
        model = EstacioCarrega
        fields = '__all__'

    def to_representation(self, instance):
        # Obtenemos la representación base
        representation = super().to_representation(instance)

        # Añadimos los campos adicionales
        representation['valoraciones'] = ValoracionEstacionSerializer(instance.valoraciones.all(), many=True).data
        representation['puntuacion_media'] = self.get_puntuacion_media(instance)
        representation['num_valoraciones'] = self.get_num_valoraciones(instance)

        return representation
    
    def get_puntuacion_media(self, obj):
        valoraciones = obj.valoraciones.all()
        if not valoraciones:
            return None
        return round(sum(v.puntuacion for v in valoraciones) / len(valoraciones), 1)
    
    def get_num_valoraciones(self, obj):
        return obj.valoraciones.count()

class TextItemSerializer(serializers.ModelSerializer):
    text = serializers.SerializerMethodField()
    class Meta:
        model = TextItem
        fields = ['id', 'key', 'text']
    
    def get_text(self, obj):
        # Obtener el idioma del usuario si está autenticado
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            lang = request.user.idioma.lower()
            if lang == 'catala':
                lang = 'ca'
            elif lang == 'castellano':
                lang = 'es'
            elif lang == 'english':
                lang = 'en'
        else:
            # Usar el idioma del sistema si no hay usuario autenticado
            lang = get_language()
            
        # Intentar obtener el texto en el idioma correspondiente
        text_field = f'text_{lang}'
        if hasattr(obj, text_field) and getattr(obj, text_field):
            return getattr(obj, text_field)
        
        # Fallback al texto por defecto
        return obj.text

class TrofeoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trofeo
        fields = ['id_trofeo', 'nombre', 'descripcion', 'puntos_necesarios']

class UsuarioTrofeoSerializer(serializers.ModelSerializer):
    trofeo = TrofeoSerializer(read_only=True)
    
    class Meta:
        model = UsuarioTrofeo
        fields = ['trofeo', 'fecha_obtencion']
from rest_framework import serializers
from .models import ReporteEstacion, EstacioCarrega, Usuario

class ReporteEstacionSerializer(serializers.ModelSerializer):
    usuario_reporta = UsuarioSerializer(read_only=True)
    estacion = EstacioCarregaSerializer(read_only=True)
    tipo_error_display = serializers.CharField(source='get_tipo_error_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    estacion_id = serializers.PrimaryKeyRelatedField(
        queryset=EstacioCarrega.objects.all(),
        source='estacion',
        write_only=True,
        help_text="ID (id_punt) de la estación a reportar."
    )

    class Meta:
        model = ReporteEstacion
        fields = [
            'id',
            'estacion',
            'usuario_reporta',
            'tipo_error',
            'tipo_error_display',
            'comentario_usuario',
            'estado',
            'estado_display',
            'fecha_reporte',
            'fecha_ultima_modificacion',
            'estacion_id',
        ]
        read_only_fields = [
            'id',
            'usuario_reporta',
            'estacion',
            'tipo_error_display',
            'estado',
            'estado_display',
            'fecha_reporte',
            'fecha_ultima_modificacion',
        ]

class TrofeoSerializerWithTranslation(serializers.ModelSerializer):
    nombre_traducido = serializers.SerializerMethodField()
    descripcion_traducida = serializers.SerializerMethodField()
    
    class Meta:
        model = Trofeo
        fields = ['id_trofeo', 'nombre', 'descripcion', 'puntos_necesarios', 'nombre_traducido', 'descripcion_traducida']
    
    def get_nombre_traducido(self, obj):
        lang = self._resolve_language()
        key = self._resolve_trophy_key(obj.nombre, "name")
        if key and lang:
            translated = self._get_translated_text(key, lang)
            if translated:
                return translated
        return obj.nombre

    def _resolve_language(self):
        request = self.context.get('request')
        
        # Lógica similar a TextItemSerializer
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user_lang = request.user.idioma.lower()
            if user_lang == 'catala':
                return 'ca'
            elif user_lang == 'castellano':
                return 'es'
            elif user_lang == 'english':
                return 'en'
        
        # Fallback al idioma del sistema, pero con validación
        system_lang = get_language()
        if system_lang:
            lang_code = system_lang[:2]
            if lang_code in ['ca', 'es', 'en']:
                return lang_code
        
        # Fallback final
        return 'es'

    def _resolve_trophy_key(self, nombre, suffix):
        mapping = [
            (["Bronze", "Bronce"], "trophy_bronze_"),
            (["Silver", "Plata"], "trophy_silver_"),
            (["Gold", "Oro"], "trophy_gold_"),
            (["Platinum", "Platino"], "trophy_platinum_"),
        ]
        for keywords, base in mapping:
            if any(word in nombre for word in keywords):
                return f"{base}{suffix}"
        return None

    def _get_translated_text(self, key, lang):
        try:
            text_item = TextItem.objects.get(key=key)
            return getattr(text_item, f'text_{lang}', None)
        except TextItem.DoesNotExist:
            return None

    
    def get_descripcion_traducida(self, obj):
        lang = self._resolve_language()
        key = self._resolve_trophy_key(obj.nombre, "description")
        if key and lang:
            translated = self._get_translated_text(key, lang)
            if translated:
                return translated
        return obj.descripcion