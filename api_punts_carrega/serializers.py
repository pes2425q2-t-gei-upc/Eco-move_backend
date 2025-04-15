from rest_framework import serializers
from .models import EstacioCarrega, Punt, TipusCarregador, Reserva, Vehicle, ModelCotxe, RefugioClimatico, PuntEmergencia, Usuario


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
            'dni', 'idioma', 'telefon', 'descripcio', 'is_admin'
        ]
        read_only_fields = ['id']