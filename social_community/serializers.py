from rest_framework import serializers
from .models import Missatge, Chat, PuntEmergencia

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = '__all__'
        
class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntEmergencia
        fields = '__all__'
        read_only_fields = ['id_emergencia', 'timestamp', 'sender']
        
class MessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Missatge
        fields = '__all__'
        ordering = ['timestamp']
        read_only_fields = ['timestamp', 'sender']