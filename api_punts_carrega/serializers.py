from datetime import datetime

from django.template.defaultfilters import date
from rest_framework import serializers
from .models import (
    EstacioCarrega,
    Punt,
    TipusCarregador,
    Reserva,
    Vehicle,
    ModelCotxe,
    RefugioClimatico,
   
    Usuario,
    ValoracionEstacion,
    TextItem,
    Idiomas
)
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

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


class RefugioClimaticoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefugioClimatico
        fields = ['id_punt', 'nombre', 'lat', 'lng', 'direccio', 'numero_calle']

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id', 'first_name', 'last_name', 'email', 'username',
            'idioma', 'telefon', 'descripcio', 'is_admin', 'punts','foto'
        ]
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
        #pk_field='id_punt'
    )
    vehicle = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        #pk_field='id_punt',
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
    class Meta:
        model = TextItem
        fields = ['__all__']
