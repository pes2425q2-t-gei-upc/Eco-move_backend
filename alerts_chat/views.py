from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import  (
    PuntEmergencia,
    Missatge,
    Chat,
)
from .serializers import ( 
    ChatSerializer,
    AlertSerializer,
    MessagesSerializer,
)

class AlertsViewSet(viewsets.ModelViewSet):
    queryset = PuntEmergencia.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Create a new alert
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
        
    # List all active alerts

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Create a new chat from an alert
    @action(detail=False, methods=['post'], url_path='create_chat/(?P<pk>[^/.]+)')
    def create_chat(self, request, alert_id=None):
        alert = get_object_or_404(PuntEmergencia, pk=alert_id)
        
        # Check that the alert is active
        if not alert.is_active:
            return Response({"error": "Alert is not active."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Prevent multiple chats for the same alert ???
        
        chat = Chat.objects.create(
            alerta=alert,
            creador=request.user,
            receptor=alert.sender,
        )
        serializer = self.get_serializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    # Get the messages of a chat
    @action(detail=True, methods=['get'], url_path="messages")
    def get_messages(self, request, pk=None):
        chat = self.get_object()
        messages = chat.missatges.all()
        serializer = MessagesSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Missatge.objects.all()
    serializer_class = MessagesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # Create a new message
    def create_message(self, serializer):
        # assume chatid
        chat_id = self.request.data.get("chat")
        chat = self.get_object(Chat, id=chat_id)
        
        # Ensure that the sender is part of the chat
        if self.request.user != chat.creador and self.request.user != chat.receptor:
            return Response({"error": "You are not part of this chat."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer.save(remitent=self.request.user, chat=chat)