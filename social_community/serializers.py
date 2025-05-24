from rest_framework import serializers
from .models import Missatge, Chat, PuntEmergencia, Report

class ChatSerializer(serializers.ModelSerializer):
    creador_username = serializers.CharField(source='creador.username', read_only=True)
    creador_first_name = serializers.CharField(source='creador.first_name', read_only=True)
    creador_last_name = serializers.CharField(source='creador.last_name', read_only=True)
    receptor_username = serializers.CharField(source='receptor.username', read_only=True)
    receptor_first_name = serializers.CharField(source='receptor.first_name', read_only=True)
    receptor_last_name = serializers.CharField(source='receptor.last_name', read_only=True)
    
    class Meta:
        model = Chat
        fields = [
            'id',
            'alerta',
            'creador',
            'creador_username',
            'creador_first_name',
            'creador_last_name',
            'receptor',
            'receptor_username',
            'receptor_first_name',
            'receptor_last_name',
            'activa',
            'inicida_en']
        
class AlertSerializer(serializers.ModelSerializer):

    sender_email = serializers.SerializerMethodField()


    class Meta:
        model = PuntEmergencia
        fields = '__all__'
    
    def get_sender_email(self, obj):
        return obj.sender.email if obj.sender else 'Unknown Email'

        
class MessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Missatge
        fields = '__all__'
        ordering = ['timestamp']
        read_only_fields = ['timestamp', 'sender']
    
class ReportSerializer(serializers.ModelSerializer):
    creador_username = serializers.CharField(source='creador.username', read_only=True)
    creador_first_name = serializers.CharField(source='creador.first_name', read_only=True)
    creador_last_name = serializers.CharField(source='creador.last_name', read_only=True)
    receptor_username = serializers.CharField(source='receptor.username', read_only=True)
    receptor_first_name = serializers.CharField(source='receptor.first_name', read_only=True)
    receptor_last_name = serializers.CharField(source='receptor.last_name', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id_report',
            'descripcio',
            'creador',
            'creador_username',
            'creador_first_name',
            'creador_last_name',
            'receptor',
            'receptor_username',
            'receptor_first_name',
            'receptor_last_name',
            'is_active',
            'timestamp'
        ]
        read_only_fields = ['id_report', 'timestamp', 'creador']