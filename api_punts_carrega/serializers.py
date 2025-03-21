from rest_framework import serializers
from .models import PuntCarrega, EstacioCarrega, Punt, Ubicacio, TipusCarregador, Reserva

class UbicacioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicacio
        fields = '__all__'

class PuntSerializer(serializers.ModelSerializer):
    class Meta:
        model = Punt
        fields = '__all__'

class EstacioCarregaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstacioCarrega
        fields = ['id_estacio', 'gestio', 'tipus_acces', 'nplaces']


class TipusCarregadorSerializer(serializers.ModelSerializer):   
    class Meta:
        model = TipusCarregador
        fields = '__all__'
    
class PuntCarregaSerializer(serializers.ModelSerializer):
    tipus_Carregador = TipusCarregadorSerializer(many = True,read_only = True)
    class Meta:
        model = PuntCarrega
        fields = ['potencia', 'tipus_velocitat', 'tipus_Carregador'] 


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
