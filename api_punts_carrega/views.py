from urllib import request
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view,action
from rest_framework.response import Response

from .models import Ubicacio, Punt, EstacioCarrega, PuntCarrega,TipusCarregador
from .serializers import (
    UbicacioSerializer, 
    PuntSerializer,
    EstacioCarregaSerializer, 
    PuntCarregaSerializer,
    NearestPuntCarregaSerializer,
    TipusCarregadorSerializer,
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
            #if ubicacio_lat and ubicacio_lng:
                #algorithme de calcul posicions, utilizar la variable distances, tambe ha de ordenar-les

        
        if not distancies:
            return Response(
                {"detail": "No se pudo calcular la distancia."},
                status=404
            )

        resultat = []
        for ubicacio, distance in distancies:
            estacio_carrega = punts_query.filter(ubicacio_estacio=ubicacio).first()
                    
            if estacio_carrega:
                distancia = distance * 111 #convertir a km
                resultat.append({
                    "ubicacio": UbicacioSerializer(ubicacio).data,
                    "estacio_carrega": EstacioCarregaSerializer(estacio_carrega).data,
                    "distancia_km": distancia
                })
            
        return Response(resultat)
