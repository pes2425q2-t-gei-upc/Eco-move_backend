from rest_framework import serializers
from .models import EstacionBici

class EstacionBiciSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstacionBici
        fields = '__all__'
