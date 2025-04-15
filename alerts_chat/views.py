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
    def get_queryset(self):
        return PuntEmergencia.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'], url_path="all")
    def list_all(self, request):
        alerts = PuntEmergencia.objects.all()
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Create a new chat from an alert
    @action(detail=True, methods=['post'], url_path='create_chat')
    def create_chat(self, request, pk=None):
        alert = get_object_or_404(PuntEmergencia, pk=pk)
        
        # Check that the alert is active
        if not alert.is_active:
            return Response({"error": "Alert is not active."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Prevent multiple chats for the same alert ???
        # if Chat.objects.filter(alerta=alert).exists():
        #     return Response({"error": "Chat already exists for this alert."}, status=status.HTTP_400_BAD_REQUEST)
        
        chat = Chat.objects.create(
            alerta=alert,
            creador=request.user,
            receptor=alert.sender,
        )
        serializer = self.get_serializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path="my_chats")
    def my_chats(self, request):
        user = request.user
        chat = chat.objects.filter(creador=user) | chat.objects.filter(receptor=user)
        serializer = self.get_serializer(chat.distinct(), many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Missatge.objects.all()
    serializer_class = MessagesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # Create a new message
    def perform_create(self, serializer):
        # assume chatid
        chat_id = self.request.data.get("chat")
        chat = self.get_object(Chat, id=chat_id)
        
        # Ensure that the sender is part of the chat
        if self.request.user not in [chat.creador, chat.receptor]:
            raise PermissionDenied("You are not part of this chat.")
        
        serializer.save(remitent=self.request.user, chat=chat)