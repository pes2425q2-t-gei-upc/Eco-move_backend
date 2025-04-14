from rest_framework import serializers
from .models import PuntEmergencia, EstacioCarrega, Punt, TipusCarregador, Reserva, Vehicle, ModelCotxe 

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
