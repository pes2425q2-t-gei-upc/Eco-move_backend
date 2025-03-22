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

from .models import Ubicacio, Punt, EstacioCarrega, PuntCarrega, TipusCarregador, Reserva
from .serializers import (
    UbicacioSerializer, 
    PuntSerializer,
    EstacioCarregaSerializer, 
    PuntCarregaSerializer,
    NearestPuntCarregaSerializer,
    TipusCarregadorSerializer,
    ReservaSerializer
)

class UbicacioViewSet(viewsets.ModelViewSet):
    queryset = Ubicacio.objects.all()
    serializer_class = UbicacioSerializer

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
            queryset = queryset.filter(estacio_carrega__id_estacio=estacio_id)

        return queryset
        
    @action(detail=False, methods=['post'])
    def crear(self, request):
        """Create a new reservation."""
        data = json.loads(request.body)
        
        # Obtener el ID de la estación (adaptado para aceptar tanto 'estacion' como 'estacio_id')
        estacio_id = data.get('estacion') or data.get('estacio_id')
        fecha_str = data.get('fecha')
        hora_str = data.get('hora')
        duracion_str = data.get('duracion')

        try:
            # Buscar la estación por id_punt o id_estacio
            try:
                estacio = EstacioCarrega.objects.get(id_punt=estacio_id)
            except EstacioCarrega.DoesNotExist:
                estacio = EstacioCarrega.objects.get(id_estacio=estacio_id)

            # Convertir la fecha
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            # Convertir la hora
            hora_inicio = datetime.strptime(hora_str, '%H:%M').time()
            
            # Convertir la duración
            if ':' in duracion_str:
                # Formato "HH:MM:SS"
                partes = duracion_str.split(':')
                horas = int(partes[0])
                minutos = int(partes[1])
                segundos = int(partes[2]) if len(partes) > 2 else 0
                duracion_td = timedelta(hours=horas, minutes=minutos, seconds=segundos)
            else:
                # Formato en segundos
                duracion_td = timedelta(seconds=int(duracion_str))
            
            hora_fin = (datetime.combine(date.today(), hora_inicio) + duracion_td).time()

            # Verificar si hay solapamiento
            reservas_existentes = Reserva.objects.filter(estacion=estacio, fecha=fecha)

            for reserva in reservas_existentes:
                hora_reserva_fin = (datetime.combine(date.today(), reserva.hora) + reserva.duracion).time()

                if not (hora_fin <= reserva.hora or hora_inicio >= hora_reserva_fin):
                    return JsonResponse({'error': 'El punt de càrrega ja està reservat en aquest horari'}, status=409)

            # Crear reserva
            reserva = Reserva.objects.create(
                estacion=estacio,
                fecha=fecha,
                hora=hora_inicio,
                duracion=duracion_td
            )
            return Response({'message': 'Reserva creada amb éxit'}, status=201)

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
    
    punts_query = EstacioCarrega.objects.all()
    
    ubicacio_ids = punts_query.values_list('ubicacio_estacio__id_ubicacio', flat=True).distinct()

    if not ubicacio_ids:
        return Response(
            {"detail": "No se encontraron puntos de carga."},
            status=404
        )
    

        min_distancia = float('inf')
        
        for ubicacio in Ubicacio.objects.filter(id_ubicacio__in=ubicacio_ids)[:50]:
            ubicacio_lat = ubicacio.lat
            ubicacio_lng = ubicacio.lng


    min_distancia = float('inf')
    
    for ubicacio in Ubicacio.objects.filter(id_ubicacio__in=ubicacio_ids):
        ubicacio_lat = ubicacio.lat
        ubicacio_lng = ubicacio.lng

        
        if ubicacio_lat and ubicacio_lng:
            distance = haversine_distance(lat, lng, ubicacio_lat, ubicacio_lng)
            ub = Ubicacio.objects.get(lat=ubicacio_lat, lng=ubicacio_lng)
            distancies.append((ub, distance))


        distancies = sorted(distancies, key=lambda x: x[1]) #The fourth element (x[3]) of each item in the list will be taken as the sorting criterion.
    
        resultat = []
        for ubicacio, distance in distancies[:40]:
            estacio_carrega = punts_query.filter(ubicacio_estacio=ubicacio).first()
                    
            if estacio_carrega:
                distancia = distance #* 111 #convertir a km (ja esta en km)
                resultat.append({
                    "estacio_carrega": EstacioCarregaSerializer(estacio_carrega).data,
                    "distancia_km": distancia                    
                })
            
        return Response(resultat)

    
    if not distancies:
        return Response(
            {"detail": "No se pudo calcular la distancia."},
            status=404
        )

    distancies = sorted(distancies, key=lambda x: x[1]) #The fourth element (x[3]) of each item in the list will be taken as the sorting criterion.

    resultat = []
    for ubicacio, distance in distancies:
        estacio_carrega = punts_query.filter(ubicacio_estacio=ubicacio).first()
                
        if estacio_carrega:
            distancia = distance #* 111 #convertir a km (ja esta en km)
            resultat.append({
                "ubicacio": UbicacioSerializer(ubicacio).data,
                "estacio_carrega": EstacioCarregaSerializer(estacio_carrega).data,
                "distancia_km": distancia                    
            })
        
    return Response(resultat)


