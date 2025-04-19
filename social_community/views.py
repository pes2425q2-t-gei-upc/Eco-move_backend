import math

from django.shortcuts import get_object_or_404
from django.db.models import Q, Max
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination

from .models import  (
    PuntEmergencia,
    Missatge,
    Chat,
)
from api_punts_carrega.models import Usuario
from .serializers import ( 
    ChatSerializer,
    AlertSerializer,
    MessagesSerializer,
)

class TenPerPagePagination(PageNumberPagination):
    page_size = 10

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
    
    @action(detail=False, methods=['get'], url_path='get_updates')
    def near_points(self, request):
        lat_usuario = request.query_params.get('lat')
        lng_usuario = request.query_params.get('lng')
        
        if not lat_usuario or not lng_usuario:
            return Response({'error': 'Faltan parámetros de ubicación (lat, lon)'}, status=400)

        lat_usuario = float(lat_usuario)
        lng_usuario = float(lng_usuario)

        puntos_cercanos = []
        for punt in PuntEmergencia.objects.filter(is_active=True):
            distancia = haversine_distance(lat_usuario, lng_usuario, punt.lat, punt.lng)
            if distancia <= 5:
                puntos_cercanos.append(punt)

        serializer = AlertSerializer(puntos_cercanos, many=True)
        return Response(serializer.data)
    
    def perform_destroy(self, instance):
        instance.delete()

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Create a new chat from an alert
    @action(detail=True, methods=['post'], url_path='create_alert_chat')
    def create_alert_chat(self, request, pk=None):
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
    
    # Start a chat with another user
    @action(detail=False, methods=['post'], url_path='create_chat')
    def create_chat(self, request):
        receptor_email = request.data.get("receptor_email")
        if not receptor_email:
            return Response({"error": "Missing 'receptor_email'."}, status=status.HTTP_400_BAD_REQUEST)
        
        if receptor_email == request.user.email:
            return Response({"error": "Cannot create a chat with yourself."}, status=status.HTTP_400_BAD_REQUEST)
        
        receptor = get_object_or_404(Usuario, email=receptor_email)
        
        # Prevent duplicate chats between users that do not involve an alert
        existing = Chat.objects.filter(
            alerta__isnull=True
        ).filter(
            Q(creador=request.user, receptor=receptor) | 
            Q(creador=receptor, receptor=request.user)
        ).first()
        
        if existing:
            return Response({"error": "Chat already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        chat = Chat.objects.create(creador=request.user, receptor=receptor, alerta=None)
        serializer = self.get_serializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path="my_chats")
    def my_chats(self, request):
        user = request.user
        chats = Chat.objects.filter(
            Q(creador=request.user) | Q(receptor=request.user)
        ).annotate(
            last_msg_time=Max("missatges__timestamp")
        ).order_by('-last_msg_time')
        
        serializer = self.get_serializer(chats.distinct(), many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path="search")
    def search_chats(self, request):
        query = request.query_params.get("q", "").strip()
        user = request.user
        chats = Chat.objects.filter(Q(creador=user) | Q(receptor=user))
        
        if query:
            chats = chats.filter(
                Q(creador__username__icontains=query, receptor=user) |
                Q(receptor__username__icontains=query, creador=user)
            )
            
        serializer = self.get_serializer(chats.distinct(), many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path="messages", name="chat-get-messages")
    def get_messages(self, request, pk=None):
        chat = get_object_or_404(Chat, pk=pk)
        
        # Ensure that the sender is part of the chat
        if self.request.user not in [chat.creador, chat.receptor]:
            raise PermissionDenied("You are not part of this chat.")
        
        paginator = TenPerPagePagination()
        messages = chat.missatges.all().order_by('-timestamp')
        page = paginator.paginate_queryset(messages, request)
        
        # Auto mark messages in this page as read if the current user is the recipient of the messages
        unread_messages = [msg for msg in page if not msg.is_read and msg.sender != self.request.user]
        for msg in unread_messages:
            msg.is_read = True
            msg.save()
        
        serializer = MessagesSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Missatge.objects.all()
    serializer_class = MessagesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # Create a new message
    def perform_create(self, serializer):
        # assume chatid
        chat_id = self.request.data.get("chat")
        chat = get_object_or_404(Chat, id=chat_id)
        
        # Ensure that the sender is part of the chat
        if self.request.user not in [chat.creador, chat.receptor]:
            raise PermissionDenied("You are not part of this chat.")
        
        serializer.save(sender=self.request.user, chat=chat)
        
    def partial_update(self, request, *args, **kwargs):
        if 'is_read' in request.data and request.data['is_read'] is False:
            raise ValidationError("Cannot mark a message as unread.")

        return super().partial_update(request, *args, **kwargs)



def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6378.0
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    
    return distance