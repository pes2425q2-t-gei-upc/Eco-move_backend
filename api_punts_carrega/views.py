import json
from urllib import request

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import api_view,action
from rest_framework.response import Response

import math

from .models import Ubicacio, Punt, EstacioCarrega, PuntCarrega, TipusCarregador, Reserva
from .serializers import (
    UbicacioSerializer, 
    PuntSerializer,
    EstacioCarregaSerializer, 
    PuntCarregaSerializer,
    NearestPuntCarregaSerializer,
    TipusCarregadorSerializer,
    ReservaSerializer,  
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
        
        distancies = []
    
        min_distancia = float('inf')
        
        for ubicacio in Ubicacio.objects.filter(id_ubicacio__in=ubicacio_ids):
            ubicacio_lat = ubicacio.lat
            ubicacio_lng = ubicacio.lng

            
            if ubicacio_lat and ubicacio_lng:
                distance = haversine_distance(lat, lng, ubicacio_lat, ubicacio_lng)
                ub = Ubicacio.objects.get(lat=ubicacio_lat, lng=ubicacio_lng)
                distancies.append((ub, distance))

        
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

@csrf_exempt
def crear_reserva(request):
        if request.method == 'POST':
            data = json.loads(request.body)
            estacio_id = data.get('estacio_id')
            fecha = data.get('fecha')
            hora = data.get('hora')
            duracion = data.get('duracion')

            try:
                estacio = EstacioCarrega.objects.get(id_estacio=estacio_id)
                reserva = Reserva.objects.create(
                    estacio=estacio,
                    fecha=fecha,
                    hora=hora,
                    duracion=duracion
                )
                return JsonResponse({'message': 'Reserva creada con éxito'}, status=201)
            except EstacioCarrega.DoesNotExist:
                return JsonResponse({'error': 'Estación no encontrada'}, status=404)
        return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def modificar_reserva(request, reserva_id):
    if request.method == 'PUT':
        try:
            reserva = Reserva.objects.get(id=reserva_id)
            data = json.loads(request.body)
            
            
            if 'fecha' in data:
                reserva.fecha = data['fecha']
            if 'hora' in data:
                reserva.hora = data['hora']
            if 'duracion' in data:
                reserva.duracion = data['duracion']
            
            '''
            if 'estacio_id' in data:
                try:
                    estacio = EstacioCarrega.objects.get(id_estacio=data['estacio_id'])
                    reserva.estacio = estacio
                except EstacioCarrega.DoesNotExist:
                    return JsonResponse({'error': 'Estación no encontrada'}, status=404)'''
            
            
            reserva.save()
            return JsonResponse({'message': 'Reserva actualizada con éxito'}, status=200)
        except Reserva.DoesNotExist:
            return JsonResponse({'error': 'Reserva no encontrada'}, status=404)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def eliminar_reserva(request, reserva_id):
    if request.method == 'DELETE':
        try:
            reserva = Reserva.objects.get(id=reserva_id)
            reserva.delete()
            return JsonResponse({'message': 'Reserva eliminada con éxito'}, status=200)
        except Reserva.DoesNotExist:
            return JsonResponse({'error': 'Reserva no encontrada'}, status=404)
    return JsonResponse({'error': 'Método no permitido'}, status=405)