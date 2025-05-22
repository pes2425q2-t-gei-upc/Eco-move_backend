from rest_framework import serializers
from .models import EstacionBici, DisponibilidadEstacionBici, UltimaActualizacionBicing, ReservaBici

class EstacionBiciSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstacionBici
        fields = '__all__'

class EstacionBiciLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstacionBici
        fields = ['id', 'lat', 'lon']

class DisponibilidadEstacionBiciSerializer(serializers.ModelSerializer):
    ultima_actualizacion_global = serializers.SerializerMethodField()

    class Meta:
        model = DisponibilidadEstacionBici
        exclude = ['estacion']

    def get_ultima_actualizacion_global(self, obj):
        ultima = UltimaActualizacionBicing.objects.get(tipo="disponibilidad")
        return ultima.fecha_actualizacion_api if ultima else None

class EstacionBiciDetalleSerializer(serializers.ModelSerializer):
    estado = DisponibilidadEstacionBiciSerializer(read_only=True)

    class Meta:
        model = EstacionBici
        fields = ['id', 'station_id', 'name', 'address', 'lat', 'lon', 'capacity', 'is_charging_station', 'estado']

class ReservaBiciSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservaBici
        fields = '__all__'
        read_only_fields = ['usuario', 'creada_en', 'expiracion', 'activa']