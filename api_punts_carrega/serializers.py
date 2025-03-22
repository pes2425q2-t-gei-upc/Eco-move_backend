from rest_framework import serializers
from .models import PuntCarrega, EstacioCarrega, Punt, TipusCarregador, Reserva


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
    
class PuntCarregaSerializer(serializers.ModelSerializer):
    tipus_Carregador = TipusCarregadorSerializer(many = True,read_only = True)
    class Meta:
        model = PuntCarrega
        fields = '__all__'
    


class NearestPuntCarregaSerializer(serializers.ModelSerializer):
    latitud = serializers.FloatField(required=True)
    longitud = serializers.FloatField(required=True)

class Tots_els_puntsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntCarrega
        fields = '__all__'

class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = '__all__'
