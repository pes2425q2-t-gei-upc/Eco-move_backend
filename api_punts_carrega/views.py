from datetime import date, datetime, timedelta
import json
from urllib import request

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

import math

from .models import  Punt, EstacioCarrega, PuntCarrega, TipusCarregador, Reserva
from .serializers import ( 
    PuntSerializer,
    EstacioCarregaSerializer, 
    PuntCarregaSerializer,
    NearestPuntCarregaSerializer,
    TipusCarregadorSerializer,
    ReservaSerializer
)


class PuntViewSet(viewsets.ModelViewSet):
    queryset = Punt.objects.all()
    serializer_class = PuntSerializer

class TipusCarregadorViewSet(viewsets.ModelViewSet):
    queryset = TipusCarregador.objects.all()
    serializer_class = TipusCarregadorSerializer

class PuntCarregaViewSet(viewsets.ModelViewSet):
    queryset = PuntCarrega.objects.all()
    serializer_class = PuntCarregaSerializer

class EstacioCarregaViewSet(viewsets.ModelViewSet):
    queryset = EstacioCarrega.objects.all()
    serializer_class = EstacioCarregaSerializer

    
class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    
    def get_queryset(self):
        """Filter the reservations by charging station if query param is provided."""
        queryset = Reserva.objects.all()
        estacio_id = self.request.query_params.get('estacio_carrega', None)
        
        if estacio_id:
            queryset = queryset.filter(estacio_carrega_id_punt=estacio_id)

        return queryset
        
    @action(detail=False, methods=['post'])
    def crear(self, request):
        """Create a new reservation."""
        data = json.loads(request.body)
        estacio_id = data.get('id_punt')
        fecha = data.get('fecha')
        hora = data.get('hora')
        duracion = data.get('duracion')

        try:
            estacio = EstacioCarrega.objects.get(id_punt=estacio_id)

            # Convertir la hora y duración
            hora_inicio = datetime.strptime(hora, '%H:%M:%S').time()
            horas, minutos, segundos = map(int, duracion.split(':'))
            duracion_td = timedelta(hours=horas, minutes=minutos, seconds=segundos)
            hora_fin = (datetime.combine(date.today(), hora_inicio) + duracion_td).time()

            # Verificar si hay solapamiento
            reservas_existentes = Reserva.objects.filter(estacio=estacio, fecha=fecha)

            for reserva in reservas_existentes:
                hora_reserva_fin = (datetime.combine(date.today(), reserva.hora) + reserva.duracion).time()

                if not (hora_fin <= reserva.hora or hora_inicio >= hora_reserva_fin):
                    return JsonResponse({'error': 'El punt de càrrega ja està reservat en aquest horari'}, status=409)

            # Crear reserva
            reserva = Reserva.objects.create(
                estacio=estacio,
                fecha=fecha,
                hora=hora_inicio,
                duracion=duracion_td
            )
            return Response({'message': 'Reserva creada amn éxit'}, status=201)

        except EstacioCarrega.DoesNotExist:
            return Response({'error': 'Estació no trobada'}, status=404)

    @action(detail=True, methods=['put'])
    def modificar(self, request, pk=None):
        """Edit a reservation."""
        reserva = get_object_or_404(Reserva, id=pk)
        data = request.data
        
        if 'fecha' in data:
            reserva.fecha = data['fecha']
        if 'hora' in data:
            reserva.hora = data['hora']
        if 'duracion' in data:
            reserva.duracion = data['duracion']
        
        reserva.save()
        return Response({'message': 'Reserva actualizada con éxito'}, status=200)

    @action(detail=True, methods=['delete'])
    def eliminar(self, request, pk=None):
        """Delete a reservation."""
        reserva = get_object_or_404(Reserva, id=pk)
        reserva.delete()
        return Response({'message': 'Reserva eliminada con éxito'}, status=200)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Earth radius in km
    R = 6378.0
    
    # degree 2 radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine forumla
    # a = sin²(difLat/2) + cos(lat1) * cos(lat2) * sin²(difLon/2)
    # c = 2*atan2(√a, √(1-a))
    # distance = R * c

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    
    return distance

@api_view(['GET'])
def punt_mes_proper(request):
    #es podria posar altres criteris de filtratge com potencia, tipus de carrega, etc.
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')
    
    if not lat or not lng:
        return Response(
            {"error": "Se requieren los parámetros 'lat' y 'lng'"},
            status=400
        )
    
    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return Response(
            {"error": "Los valores de 'lat' y 'lng' no son numeros"},
            status=404
        )
        
    estacions = EstacioCarrega.objects.all()

    min_distancia = float('inf')
    distancies = []
    
    for estacio in estacions:      
        if estacio.lat is not None and estacio.lng is not None:
            distance = haversine_distance(lat, lng, estacio.lat, estacio.lng)
            distancies.append((estacio, distance))


    distancies = sorted(distancies, key=lambda x: x[1]) #The second element (x[1]) of each item in the list will be taken as the sorting criterion.
    distancies = distancies[:60]
    resultat = []
    
    for estacio, distance in distancies:
        # Get charging points for this station
        punts_carrega = estacio.punt_carrega.all()
        
        resultat.append({
            "estacio_carrega": EstacioCarregaSerializer(estacio).data,
            "distancia_km": distance,
            "punts_de_carrega": PuntCarregaSerializer(punts_carrega, many=True).data,                  
        })
            
    return Response(resultat)
