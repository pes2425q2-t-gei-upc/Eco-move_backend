from rest_framework import serializers
from .models import PuntCarrega, EstacioCarrega, Punt, Ubicacio, TipusCarregador

class UbicacioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicacio
        fields = '__all__'

class PuntSerializer(serializers.ModelSerializer):
    ubicacio_punt = UbicacioSerializer(read_only=True)
    ubicacio = serializers.PrimaryKeyRelatedField(
        queryset=Ubicacio.objects.all(),
        write_only=True,    
        required=True
    )
    
    class Meta:
        model = Punt
        fields = ['id_punt','ubicacio_punt','ubicacio']

    def validate(self, data):
        ubicacio = data.get('ubicacio', None)
        if ubicacio is None:
            raise serializers.ValidationError("La ubicación no puede ser nula")
        if ubicacio:
            existing_ubicacio_punt = Punt.objects.filter(ubicacio_punt=ubicacio).exists()
            existing_ubicacio_estacio = EstacioCarrega.objects.filter(ubicacio_estacio=ubicacio).exists()
            if existing_ubicacio_punt:
                raise serializers.ValidationError("La ubicación seleccionada ya está asociada a otro punto.")
            if existing_ubicacio_estacio:
                raise serializers.ValidationError("La ubicación seleccionada ya está asociada a una estación.")
        
        return data
    
    def create(self, validated_data):
        ubicacio = validated_data.pop('ubicacio')
        estacio = EstacioCarrega.objects.create(ubicacio_estacio=ubicacio, **validated_data)
        return estacio

class EstacioCarregaSerializer(serializers.ModelSerializer):
    ubicacio_estacio = UbicacioSerializer(read_only=True)
    ubicacio_id = serializers.PrimaryKeyRelatedField(
        queryset=Ubicacio.objects.all(),
        write_only=True,    
        required=True
    )

    class Meta:
        model = EstacioCarrega
        fields = ['id_estacio','ubicacio_id','ubicacio_estacio','gestio','tipus_acces']

    def validate(self, data):
        ubicacio_id = data.get('ubicacio_id', None)
        if ubicacio_id is None:
            raise serializers.ValidationError("La ubicación no puede ser nula")
        if ubicacio_id:
            existing_ubicacio_punt = Punt.objects.filter(ubicacio_punt=ubicacio_id).exists()
            existing_ubicacio_estacio = EstacioCarrega.objects.filter(ubicacio_estacio=ubicacio_id).exists()
            if existing_ubicacio_punt:
                raise serializers.ValidationError("La ubicación seleccionada ya está asociada a otro punto.")
            if existing_ubicacio_estacio:
                raise serializers.ValidationError("La ubicación seleccionada ya está asociada a una estación.")
        
        return data
    
    def create(self, validated_data):
        ubicacio = validated_data.pop('ubicacio_id')
        estacio = EstacioCarrega.objects.create(ubicacio_estacio=ubicacio, **validated_data)
        return estacio
    
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

