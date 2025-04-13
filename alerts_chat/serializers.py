from rest_framework import serializers
from .models import Missatge, Chat

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = '__all__'
        
class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Missatge
        fields = '__all__'
        
class MessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Missatge
        fields = '__all__'