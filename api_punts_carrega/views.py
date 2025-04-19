from datetime import date, datetime, timedelta
import json
import math
import requests

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db import models
from django.db.models import Avg, Count, Q
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import api_view, action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import  Punt, EstacioCarrega, TipusCarregador, Reserva, Vehicle, ModelCotxe, RefugioClimatico, PuntEmergencia, Usuario, ValoracionEstacion

from .serializers import ( 
    PuntSerializer,
    EstacioCarregaSerializer, 
    NearestPuntCarregaSerializer,
    TipusCarregadorSerializer,
    ReservaSerializer,
    VehicleSerializer,
    ModelCotxeSerializer,
    RefugioClimaticoSerializer,
    PuntEmergenciaSerializer,
    UsuarioSerializer,
    ValoracionEstacionSerializer,
    EstacioCarregaConValoracionesSerializer,

)
from .views.usuari import UsuarioViewSet

DISTANCIA_MAXIMA_KM = 5

class PuntEmergenciaViewSet(viewsets.ModelViewSet):
    queryset = PuntEmergencia.objects.all()
    serializer_class = PuntEmergenciaSerializer

    @action(detail=False, methods=['get'], url_path='get_updates')
    def ultims_punts(self, request):
        lat_usuario = request.query_params.get('lat')
        lng_usuario = request.query_params.get('lng')
        
        if not lat_usuario or not lng_usuario:
            return Response({'error': 'Faltan parámetros de ubicación (lat, lon)'}, status=400)

        lat_usuario = float(lat_usuario)
        lng_usuario = float(lng_usuario)

        puntos_cercanos = []
        for punt in PuntEmergencia.objects.all():
            distancia = haversine_distance(lat_usuario, lng_usuario, punt.lat, punt.lng)
            if distancia <= DISTANCIA_MAXIMA_KM:
                puntos_cercanos.append(punt)

        serializer = PuntEmergenciaSerializer(puntos_cercanos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='modificar')
    def modificar_punt(self, request, pk=None):
        punt = get_object_or_404(PuntEmergencia, pk=pk)
        serializer = PuntEmergenciaSerializer(punt, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Punt d\'emergència modificat correctament'})
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['delete'], url_path='eliminar')
    def eliminar_punt(self, request, pk=None):
        punt = get_object_or_404(PuntEmergencia, pk=pk)
        punt.delete()
        return Response({'message': 'Punt d\'emergència eliminat correctament'}, status=200)


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
    queryset = EstacioCarrega.objects.prefetch_related('tipus_carregador', 'valoraciones').all()
    
    def get_serializer_class(self):
        include_valoraciones = self.request.query_params.get('include_valoraciones', 'false').lower() == 'true'
        if include_valoraciones:
            return EstacioCarregaConValoracionesSerializer
        return EstacioCarregaSerializer
    
    @action(detail=True, methods=['get'])
    def valoraciones(self, request, pk=None):
        estacion = self.get_object()
        valoraciones = estacion.valoraciones.all()
        serializer = ValoracionEstacionSerializer(valoraciones, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def estadisticas_valoraciones(self, request, pk=None):
        estacion = self.get_object()
        stats = estacion.valoraciones.aggregate(
            media=Avg('puntuacion'),
            total=Count('id'),
            puntuacion_1=Count('id', filter=models.Q(puntuacion=1)),
            puntuacion_2=Count('id', filter=models.Q(puntuacion=2)),
            puntuacion_3=Count('id', filter=models.Q(puntuacion=3)),
            puntuacion_4=Count('id', filter=models.Q(puntuacion=4)),
            puntuacion_5=Count('id', filter=models.Q(puntuacion=5)),
        )
        
        # Redondear la media a 1 decimal
        if stats['media'] is not None:
            stats['media'] = round(stats['media'], 1)
            
        return Response(stats)


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

class RefugioClimaticoViewSet(viewsets.ModelViewSet):
    queryset = RefugioClimatico.objects.all()
    serializer_class = RefugioClimaticoSerializer

@api_view(['GET'])
def sincronizar_refugios(request):
    try:
        
        response = requests.get('http://nattech.fib.upc.edu:40430/api/refugios/listar/', timeout=10)
        response.raise_for_status()
        
        refugios_data = response.json()
        contador_nuevos = 0
        contador_actualizados = 0
        
        for refugio_data in refugios_data:
            
            refugio_id = refugio_data['id']
            
            # Intentar encontrar el refugio existente o crear uno nuevo
            refugio, created = RefugioClimatico.objects.update_or_create(
                id_punt=refugio_id,
                defaults={
                    'nombre': refugio_data['nombre'],
                    'lat': float(refugio_data['latitud']),
                    'lng': float(refugio_data['longitud']),
                    'direccio': refugio_data['direccion'],
                    'numero_calle': refugio_data['numero_calle'],
                }
            )
            
            if created:
                contador_nuevos += 1
            else:
                contador_actualizados += 1
        
        return Response({
            'mensaje': f'Sincronización completada. {contador_nuevos} refugios nuevos, {contador_actualizados} actualizados.',
            'total_refugios': RefugioClimatico.objects.count()
        }, status=status.HTTP_200_OK)
        
    except requests.Timeout:
        return Response({"error": "Tiempo de espera agotado al conectar con la API de refugios"}, 
                       status=status.HTTP_504_GATEWAY_TIMEOUT)
    except requests.HTTPError as e:
        return Response({"error": f"Error HTTP {e.response.status_code} al obtener datos de refugios"}, 
                       status=e.response.status_code)
    except requests.RequestException as e:
        return Response({"error": f"Error de conexión con la API de refugios: {str(e)}"}, 
                       status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        print(f"Error inesperado en sincronizar_refugios: {e}")
        return Response({'error': 'Ocurrió un error inesperado en el servidor'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def refugios_mas_cercanos(request):
    
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
            {"error": "Los valores de 'lat' y 'lng' no son números"},
            status=404
        )
        
    refugios = RefugioClimatico.objects.all()
    
    distancias = []
    
    for refugio in refugios:      
        if refugio.lat is not None and refugio.lng is not None:
            distance = haversine_distance(lat, lng, refugio.lat, refugio.lng)
            distancias.append((refugio, distance))

    distancias = sorted(distancias, key=lambda x: x[1])
    distancias = distancias[:60]  # Limitamos a los 60 más cercanos
    
    resultado = []
    
    for refugio, distance in distancias:
        resultado.append({
            "refugio": RefugioClimaticoSerializer(refugio).data,
            "distancia_km": distance,
        })
            
    return Response(resultado)

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
        vehicle_matricula = data.get('vehicle')

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


            vehicle = None
            if vehicle_matricula:
                try:
                    vehicle = Vehicle.objects.get(matricula=vehicle_matricula)
                except Vehicle.DoesNotExist:
                    return Response({'error': 'Vehicle no trobat'}, status=404)
                
                
                vehicle_carregadors = set(vehicle.model_cotxe.tipus_carregador.all().values_list('id_carregador', flat=True))
                estacio_carregadors = set(estacio.tipus_carregador.all().values_list('id_carregador', flat=True))
                
                if not vehicle_carregadors.intersection(estacio_carregadors):
                    return Response({'error': 'El vehicle no és compatible amb aquesta estació de càrrega'}, status=400)
           
            
            reserva = Reserva.objects.create(
                estacion=estacio,
                fecha=fecha,
                hora=hora_inicio,
                duracion=duracion_td,
                vehicle=vehicle
            )

            
            return Response({'message': 'Reserva creada amb éxit'}, status=201)

        except EstacioCarrega.DoesNotExist:
            return Response({'error': 'Estació no trobada'}, status=404)

    @action(detail=True, methods=['put'])
    def modificar(self, request, pk=None):
        
        reserva = get_object_or_404(Reserva, id=pk)
        data = request.data
        
       
        fecha = reserva.fecha
        hora_inicio = reserva.hora
        duracion_td = reserva.duracion
        estacio = reserva.estacion
        vehicle = reserva.vehicle
        
        
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
        
        vehicle_matricula = None
        if 'vehicle' in data:
            vehicle_matricula = data.get('vehicle')
        
        if vehicle_matricula:
            try:
                vehicle = Vehicle.objects.get(matricula=vehicle_matricula)
                
                # Verificar compatibilidad entre el vehículo y la estación de carga
                vehicle_carregadors = set(vehicle.model_cotxe.tipus_carregador.all().values_list('id_carregador', flat=True))
                estacio_carregadors = set(estacio.tipus_carregador.all().values_list('id_carregador', flat=True))
                
                if not vehicle_carregadors.intersection(estacio_carregadors):
                    return Response({'error': 'El vehicle no és compatible amb aquesta estació de càrrega'}, status=400)
            except Vehicle.DoesNotExist:
                return Response({'error': 'Vehicle no trobat'}, status=404)
            
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
        
        
        else:
            vehicle = None
        
        # Update reservation
        reserva.fecha = fecha
        reserva.hora = hora_inicio
        reserva.duracion = duracion_td
        reserva.vehicle = vehicle
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
def filtrar_per_carregador(request):
    
    estacions = EstacioCarrega.objects.prefetch_related('tipus_carregador').all()
    
    
    carregador_id = request.query_params.get('id')
    if carregador_id is not None:
        
        carregador_ids = carregador_id.split(',')
        estacions = estacions.filter(tipus_carregador__id_carregador__in=carregador_ids)
    
    
    serializer = EstacioCarregaSerializer(estacions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def obtenir_opcions_filtres(request):
    
    
    potencia_min = EstacioCarrega.objects.filter(potencia__isnull=False).order_by('potencia').values_list('potencia', flat=True).first() or 0
    potencia_max = EstacioCarrega.objects.filter(potencia__isnull=False).order_by('-potencia').values_list('potencia', flat=True).first() or 0
    
    
    velocitats = EstacioCarrega.objects.filter(tipus_velocitat__isnull=False).values_list('tipus_velocitat', flat=True).distinct()
    
    
    tipus_carregadors = TipusCarregador.objects.all()
    carregadors = []
    
    for carregador in tipus_carregadors:
        carregadors.append({
            'id': carregador.id_carregador,
            'nom': carregador.nom_tipus,
            'connector': carregador.tipus_connector,
            'corrent': carregador.tipus_corrent
        })
    
    
    resposta = {
        'potencia': {
            'min': potencia_min,
            'max': potencia_max
        },
        'velocitats': list(velocitats),
        'carregadors': carregadors
    }
    
    return Response(resposta)

@api_view(['GET'])
def filtrar_estacions(request):
    
    estacions = EstacioCarrega.objects.prefetch_related('tipus_carregador').all()
    
    
    potencia_min = request.query_params.get('potencia_min')
    if potencia_min is not None:
        try:
            potencia_min = int(potencia_min)
            estacions = estacions.filter(potencia__gte=potencia_min)
        except ValueError:
            return Response(
                {"error": "El valor de 'potencia_min' debe ser un número entero"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    
    potencia_max = request.query_params.get('potencia_max')
    if potencia_max is not None:
        try:
            potencia_max = int(potencia_max)
            estacions = estacions.filter(potencia__lte=potencia_max)
        except ValueError:
            return Response(
                {"error": "El valor de 'potencia_max' debe ser un número entero"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    
    velocitat = request.query_params.get('velocitat')
    if velocitat is not None:
        velocitats = velocitat.split(',')
        estacions = estacions.filter(tipus_velocitat__in=velocitats)


    tipus_carregador = request.query_params.get('tipus_carregador')
    if tipus_carregador is not None:
        tipus_carregador = tipus_carregador.split(',')
        estacions = estacions.filter(tipus_carregador__id_carregador__in=tipus_carregador)


    
    ciutat = request.query_params.get('ciutat')
    if ciutat is not None:
        ciutats = ciutat.split(',')
        estacions = estacions.filter(ciutat__in=ciutats)


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

class ValoracionEstacionViewSet(viewsets.ModelViewSet):
    queryset = ValoracionEstacion.objects.all()
    serializer_class = ValoracionEstacionSerializer
    
    def get_queryset(self):
        queryset = ValoracionEstacion.objects.all()
        estacion_id = self.request.query_params.get('estacion', None)
        usuario_id = self.request.query_params.get('usuario', None)
        
        if estacion_id:
            queryset = queryset.filter(estacion_id=estacion_id)
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
            
        return queryset
    
    # def perform_create(self, serializer):
    #     serializer.save(usuario=self.request.user)
    
    # def perform_update(self, serializer):
    #     valoracion = self.get_object()
    #     if valoracion.usuario != self.request.user:
    #         raise PermissionDenied("No tienes permiso para modificar esta valoración")
    #     serializer.save()
    
    # def perform_destroy(self, instance):
    #     if instance.usuario != self.request.user and not self.request.user.is_admin:
    #         raise PermissionDenied("No tienes permiso para eliminar esta valoración")
    #     instance.delete()
