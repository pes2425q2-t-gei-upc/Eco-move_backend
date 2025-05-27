import math

from django.shortcuts import get_object_or_404
from django.db.models import Q, Max
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from datetime import timedelta
import json

from .models import  (
    PuntEmergencia,
    Missatge,
    Chat,
    Report,
)
from api_punts_carrega.models import Usuario
from .serializers import ( 
    ChatSerializer,
    AlertSerializer,
    MessagesSerializer,
    ReportSerializer,
)

class TenPerPagePagination(PageNumberPagination):
    page_size = 10

class AlertsViewSet(viewsets.ModelViewSet):
    queryset = PuntEmergencia.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.bloqueado == True:
            raise PermissionDenied("Usuario bloqueado: no puedes crear alertas.")
        
        serializer.save(sender=self.request.user)

           
    def get_queryset(self):
        return PuntEmergencia.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'], url_path="all")
    def list_all(self, request):
        alerts = PuntEmergencia.objects.all()
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='polling_alertes')
    def polling_alertes(self, request):
        """
        Lat,lon cordenades necessaries per calcular la distancia entre el punt d'alerta i l'usuari.
        Retorna totes les alertes actives ordenades per distancia al punt d'alerta de l'usuari.
        Si es proporciona el paràmetre 'since', només es retornaran les alertes que s'han creat després d'aquest timestamp. per poder aixi no haver de carregar totes les alertes cada cop.
        tambe es pot filtrar per alertes actives o no actives, per defecte son actives.
        """
        lat_usuario = request.query_params.get('lat')
        lng_usuario = request.query_params.get('lng')
        active_only = request.query_params.get('active_only', 'true').lower() == 'true'
        since_param = request.query_params.get('since')

        if request.user.bloqueado == True:
            return Response(
                {'error': 'Usuario bloqueado: no puedes ver alertas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not lat_usuario or not lng_usuario:
            return Response(
                {'error': 'Se requieren parámetros de ubicación (lat, lng)'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            lat_usuario = float(lat_usuario)
            lng_usuario = float(lng_usuario)
        except ValueError:
            return Response(
                {'error': 'Las coordenadas deben ser valores numéricos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if since_param:
            try:
                since_time = timezone.datetime.fromtimestamp(float(since_param), tz=timezone.get_current_timezone())
                alerts_queryset = PuntEmergencia.objects.filter(timestamp__gt=since_time)
            except (ValueError, OverflowError, TypeError):
                return Response(
                    {'error': 'Formato de timestamp inválido. Use timestamp Unix (segundos desde epoch).'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            alerts_queryset = PuntEmergencia.objects.all()
        
        if active_only:
            alerts_queryset = alerts_queryset.filter(is_active=True)
            
        alerts_with_distance = []
        for alert in alerts_queryset:
            distance = haversine_distance(lat_usuario, lng_usuario, alert.lat, alert.lng)
            alerts_with_distance.append((alert, distance))
        
        alerts_with_distance.sort(key=lambda x: x[1])
        sorted_alerts = [alert for alert, _ in alerts_with_distance]
        
        serializer = self.get_serializer(sorted_alerts, many=True)
        
        current_timestamp = timezone.now().timestamp()
        
        return Response({
            'alerts': serializer.data,
            'timestamp': current_timestamp,
        })
    
    def perform_destroy(self, instance):
        instance.delete()

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    
    USUARIO_BLOQUEADO_CHAT_ERROR = "Usuario bloqueado: no puedes crear un chat."

    @action(detail=True, methods=['post'], url_path='create_alert_chat')
    def create_alert_chat(self, request, pk=None):
        alert = get_object_or_404(PuntEmergencia, pk=pk)

        if request.user.bloqueado == True:
            return Response({"error": self.USUARIO_BLOQUEADO_CHAT_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        
        if alert.sender.bloqueado == True:
            return Response({"error": self.USUARIO_BLOQUEADO_CHAT_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        
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
        if receptor.bloqueado == True:
            return Response({"error": "Usuario bloquedo: no puedes chatear con el."}, status=status.HTTP_400_BAD_REQUEST)
        creador = request.user
        if creador.bloqueado == True:
            return Response({"error": "Usuario bloqueado: no puedes crear un chat."}, status=status.HTTP_400_BAD_REQUEST)
        
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

        if self.request.user.bloqueado == True:
            raise PermissionDenied("Usuario bloqueado: no puedes enviar mensajes.")
        
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

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Admin users can see all reports
        if self.request.user.is_staff:
            return Report.objects.all().order_by('-timestamp')
        # Regular users can only see reports they created
        return Report.objects.filter(creador=self.request.user).order_by('-timestamp')
    
    def perform_create(self, serializer):
        serializer.save(creador=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='report_from_chat')
    def report_from_chat(self, request):
        """
        Create a report based on a chat conversation.
        Requires chat_id and descripcio in the payload.
        """
        chat_id = request.data.get('chat_id')
        descripcio = request.data.get('descripcio')
        
        if not chat_id or not descripcio:
            return Response(
                {'error': 'Se requieren los campos chat_id y descripcio'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get the chat
        chat = get_object_or_404(Chat, id=chat_id)
        
        # Verify the user is part of the chat
        if request.user not in [chat.creador, chat.receptor]:
            return Response(
                {'error': 'No puedes reportar a un usuario con el que no tienes un chat'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Determine which user to report (the other user in the chat)
        receptor = chat.receptor if request.user == chat.creador else chat.creador
        
        # Check if a report for this user from this chat already exists
        existing_report = Report.objects.filter(
            creador=request.user,
            receptor=receptor,
            is_active=True
        ).first()
        
        if existing_report:
            return Response(
                {'error': 'Ya has reportado a este usuario y el reporte sigue activo'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Create the report
        report = Report.objects.create(
            creador=request.user,
            receptor=receptor,
            descripcio=descripcio
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='my_reports')
    def my_reports(self, request):
        """
        Get all reports created by the authenticated user
        """
        reports = Report.objects.filter(creador=request.user).order_by('-timestamp')
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)
    