from rest_framework import serializers
from .models import PuntCarrega, EstacioCarrega, Punt, Ubicacio, TipusCarregador

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
        fields = '__all__'
    
class PuntCarregaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntCarrega
        fields = '__all__'


class TipusCarregadorSerializer(serializers.ModelSerializer):   
    class Meta:
        model = TipusCarregador
        fields = '__all__'

class NearestPuntCarregaSerializer(serializers.ModelSerializer):
    latitud = serializers.FloatField(required=True)
    longitud = serializers.FloatField(required=True)

