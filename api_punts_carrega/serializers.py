from rest_framework import serializers
from .models import EstacioCarrega, Punt, TipusCarregador, Reserva, Vehicle, ModelCotxe, RefugioClimatico, PuntEmergencia, Usuario, ValoracionEstacion


class PuntEmergenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntEmergencia
        fields = '__all__'

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

class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = '__all__'

class RefugioClimaticoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefugioClimatico
        fields = ['id_punt', 'nombre', 'lat', 'lng', 'direccio', 'numero_calle']

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id', 'first_name', 'last_name', 'email', 'username',
            'idioma', 'telefon', 'descripcio', 'is_admin', 'punts'
        ]
        read_only_fields = ['id', 'punts']

class UsuarioUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'telefon', 'descripcio', 'idioma']

    def validate_telefon(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("El teléfono debe contener solo números.")
        return value

class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefon', 'descripcio', 'idioma', 'password']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)  # Encripta correctamente la contraseña
        user.username = user.email  # Si quieres forzar esto
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
