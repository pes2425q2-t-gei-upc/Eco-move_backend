from datetime import date, datetime, timedelta
import json
import math
import requests

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from .models import  Punt, EstacioCarrega, TipusCarregador, Reserva, Vehicle, ModelCotxe
from .serializers import ( 
    PuntSerializer,
    EstacioCarregaSerializer, 
    NearestPuntCarregaSerializer,
    TipusCarregadorSerializer,
    ReservaSerializer,
    VehicleSerializer,
    ModelCotxeSerializer
)

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

class ModelCotxeViewSet(viewsets.ModelViewSet):
    queryset = ModelCotxe.objects.all()
    serializer_class = ModelCotxeSerializer


class PuntViewSet(viewsets.ModelViewSet):
    queryset = Punt.objects.all()
    serializer_class = PuntSerializer

class TipusCarregadorViewSet(viewsets.ModelViewSet):
    queryset = TipusCarregador.objects.all()
    serializer_class = TipusCarregadorSerializer


class EstacioCarregaViewSet(viewsets.ModelViewSet):
    queryset = EstacioCarrega.objects.prefetch_related('tipus_carregador').all()
    serializer_class = EstacioCarregaSerializer


class ReservaSerializer(serializers.ModelSerializer):
    fecha = serializers.DateField(format='%d/%m/%Y')
    hora = serializers.TimeField(format='%H:%M')

    class Meta:
        model = Reserva
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['fecha'] = instance.fecha.strftime('%d/%m/%Y')
        representation['hora'] = instance.hora.strftime('%H:%M')
        return representation


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
        data = json.loads(request.body)
        
        estacio_id = data.get('estacion')
        fecha_str = data.get('fecha')
        hora_str = data.get('hora')
        duracion_str = data.get('duracion')

        try:
            
            try:
                estacio = EstacioCarrega.objects.get(id_punt=estacio_id)
            except EstacioCarrega.DoesNotExist:
                estacio = EstacioCarrega.objects.get(id_punt=estacio_id)
            

            # Convertir la fecha
            fecha = datetime.strptime(fecha_str, '%d/%m/%Y').date()
            
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

            placesReservades = 0

            for reserva_existente in reservas_existentes:
                hora_reserva_fin = (datetime.combine(date.today(), reserva_existente.hora) + 
                                reserva_existente.duracion).time()
                
                if not (hora_fin <= reserva_existente.hora or hora_inicio >= hora_reserva_fin):
                    placesReservades += 1
                    if placesReservades >= int(estacio.nplaces):
                        return Response({'error': 'No hi ha places lliures en aquest punt de càrrega en aquesta data i hora'}, status=409)

           
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
        
        reserva = get_object_or_404(Reserva, id=pk)
        data = request.data
        
        # Get current values or updated values from request
        fecha = reserva.fecha
        hora_inicio = reserva.hora
        duracion_td = reserva.duracion
        estacio = reserva.estacion
        
        # Update values if provided in request
        if 'fecha' in data:
            fecha_str = data.get('fecha')
            fecha = datetime.strptime(fecha_str, '%d/%m/%Y').date()
        
        if 'hora' in data:
            hora_str = data.get('hora')
            if isinstance(hora_str, str):
                hora_inicio = datetime.strptime(hora_str, '%H:%M').time()
            else:
                hora_inicio = hora_str
        
        if 'duracion' in data:
            duracion_str = data.get('duracion')
            if isinstance(duracion_str, str):
                if ':' in duracion_str:
                    # Format "HH:MM:SS"
                    partes = duracion_str.split(':')
                    horas = int(partes[0])
                    minutos = int(partes[1])
                    segundos = int(partes[2]) if len(partes) > 2 else 0
                    duracion_td = timedelta(hours=horas, minutes=minutos, seconds=segundos)
                else:
                    # Format in seconds
                    duracion_td = timedelta(seconds=int(duracion_str))
            else:
                duracion_td = duracion_str
        
        # Calculate end time
        hora_fin = (datetime.combine(date.today(), hora_inicio) + duracion_td).time()
        
        # Check for overlapping reservations
        reservas_existentes = Reserva.objects.filter(estacion=estacio, fecha=fecha).exclude(id=pk)
        
        placesReservades = 0

        for reserva_existente in reservas_existentes:
            hora_reserva_fin = (datetime.combine(date.today(), reserva_existente.hora) + 
                            reserva_existente.duracion).time()
            
            if not (hora_fin <= reserva_existente.hora or hora_inicio >= hora_reserva_fin):
                placesReservades += 1
                if placesReservades >= int(estacio.nplaces):
                    return Response({'error': 'No hi ha places lliures en aquest punt de càrrega en aquesta data i hora'}, status=409)
                
        
        # Update reservation
        reserva.fecha = fecha
        reserva.hora = hora_inicio
        reserva.duracion = duracion_td
        reserva.save()
    
        return Response({'message': 'Reserva actualizada con éxito'}, status=200)

    @action(detail=True, methods=['delete'])
    def eliminar(self, request, pk=None):
        
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
        
        resultat.append({
            "estacio_carrega": EstacioCarregaSerializer(estacio).data,
            "distancia_km": distance,
        })
            
    return Response(resultat)


@api_view(['GET'])
def filtrar_per_potencia(request):
   
    estacions = EstacioCarrega.objects.all()
    

    potencia_min = request.query_params.get('min')
    if potencia_min is not None:
        try:
            potencia_min = int(potencia_min)
            estacions = estacions.filter(potencia__gte=potencia_min)
        except ValueError:
            return Response(
                {"error": "El valor de 'min' debe ser un número entero"},
                status=status.HTTP_400_BAD_REQUEST
            )

    potencia_max = request.query_params.get('max')
    if potencia_max is not None:
        try:
            potencia_max = int(potencia_max)
            estacions = estacions.filter(potencia__lte=potencia_max)
        except ValueError:
            return Response(
                {"error": "El valor de 'max' debe ser un número entero"},
                status=status.HTTP_400_BAD_REQUEST
            )
    

    serializer = EstacioCarregaSerializer(estacions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def filtrar_per_velocitat(request):
    
    estacions = EstacioCarrega.objects.all()
    
    velocitat = request.query_params.get('velocitat')
    if velocitat is not None:
        # los tipos de velocidades se separan por comas en la query
        velocitats = velocitat.split(',')
        estacions = estacions.filter(tipus_velocitat__in=velocitats)
    
    serializer = EstacioCarregaSerializer(estacions, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def obtenir_preu_actual_kwh(request):
    """Obtiene el precio del kWh en Cataluña desde la API de Red Eléctrica de España (REE)."""

    hoy = datetime.now().date()
    fecha_str = hoy.strftime("%d/%m/%Y")
    fecha_inicio = f"{fecha_str}T00:00"
    fecha_fin = f"{fecha_str}T23:59"

    url = (
        "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
        f"?start_date={fecha_inicio}&end_date={fecha_fin}&time_trunc=hour"
    )


    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json' # Añadir Accept por si acaso
    }


    try:

        response = requests.get(url, headers=headers, timeout=10)


        response.raise_for_status()

        data = response.json()

        precios_kwh_hoy = []
        if "included" in data and data["included"]:
            indicador_precios = data["included"][0]
            if "attributes" in indicador_precios and "values" in indicador_precios["attributes"]:
                valores_horarios = indicador_precios["attributes"]["values"]

                for valor_hora in valores_horarios:
                    precio_mwh = valor_hora.get("value")
                    timestamp_str = valor_hora.get("datetime")

                    if precio_mwh is not None and timestamp_str:
                        try:
                            precio_kwh = float(precio_mwh) / 1000
                            hora_dt = datetime.fromisoformat(timestamp_str)
                            hora_simple = hora_dt.strftime("%H:%M")

                            precios_kwh_hoy.append({
                                "hora": hora_simple,
                                "precio_kwh": round(precio_kwh, 5)
                            })
                        except (ValueError, TypeError) as e:
                            print(f"Error procesando valor horario {valor_hora}: {e}")
                            continue

        if not precios_kwh_hoy:
            return Response(
                {"error": "No se encontraron datos de precios horarios para hoy en la respuesta de la API"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "fecha": fecha_str,
            "precios_hoy": precios_kwh_hoy,
            "unidad": "€/kWh",
            "fuente": "Red Eléctrica de España (REE)"
        }, status=status.HTTP_200_OK)

    except requests.Timeout:
        return Response({"error": "Tiempo de espera agotado al conectar con la API de REE"}, status=status.HTTP_504_GATEWAY_TIMEOUT)
    except requests.HTTPError as e:
        error_detail = f"Error HTTP {response.status_code}"
        try:
            error_data = response.json()
            if "errors" in error_data and error_data["errors"]:
                error_detail = error_data["errors"][0].get("detail", error_detail)
        except json.JSONDecodeError:
            pass
        # Devolvemos el detalle del error y el status code original del error HTTP
        return Response({"error": f"Error al obtener datos de REE: {error_detail}"}, status=response.status_code)
    except requests.RequestException as e:
        return Response({"error": f"Fallo en la conexión con la API de REE: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        print(f"Error inesperado en obtener_preus_dia_actual: {e}")
        return Response({'error': 'Ocurrió un error inesperado en el servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)