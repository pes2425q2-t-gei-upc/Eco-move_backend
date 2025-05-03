from datetime import date, datetime, timedelta
from rest_framework.permissions import IsAuthenticated, AllowAny
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
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import  (
    Punt,
    EstacioCarrega,
    TipusCarregador,
    Reserva,
    Vehicle,
    ModelCotxe,
    RefugioClimatico,
    Usuario,
    ValoracionEstacion,
    TextItem,
    Idiomas
)
from .permissions import EsElMismoUsuarioOReadOnly


from .serializers import ( 
    PuntSerializer,
    EstacioCarregaSerializer,
    NearestPuntCarregaSerializer,
    TipusCarregadorSerializer,
    ReservaSerializer,
    VehicleSerializer,
    ModelCotxeSerializer,
    RefugioClimaticoSerializer,
    UsuarioSerializer,
    ValoracionEstacionSerializer,
    EstacioCarregaConValoracionesSerializer,
    TextItemSerializer,
    RegisterSerializer,
    PerfilPublicoSerializer,
    FotoPerfilSerializer,
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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Devuelve reservas del usuario autenticado, filtrando opcionalmente por estación y día (DD/MM/YYYY).
        """
        try:
            user = self.request.user
            if not user.is_authenticated:
                return Reserva.objects.none()
            queryset = Reserva.objects.filter(usuario=user)
        except AttributeError:
            return Reserva.objects.none()

        estacio_id_param = self.request.query_params.get('estacion_carrega')
        if estacio_id_param:
            queryset = queryset.filter(estacion__id_punt=estacio_id_param)

        dia_str = self.request.query_params.get('dia')
        if dia_str:
            try:
                dia_obj = datetime.strptime(dia_str, '%d/%m/%Y').date()
                queryset = queryset.filter(fecha=dia_obj)
                return queryset.select_related('usuario', 'estacion', 'vehicle')
            except ValueError:
                print(f"WARN: Formato fecha inválido para ?dia= : {dia_str}")

        return queryset.select_related('usuario', 'estacion', 'vehicle')


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


            fecha = datetime.strptime(fecha_str, '%d/%m/%Y').date()

            hora_inicio = datetime.strptime(hora_str, '%H:%M').time()

            if ':' in duracion_str:
                partes = duracion_str.split(':')
                horas = int(partes[0])
                minutos = int(partes[1])
                segundos = int(partes[2]) if len(partes) > 2 else 0
                duracion_td = timedelta(hours=horas, minutes=minutos, seconds=segundos)
            else:
                duracion_td = timedelta(seconds=int(duracion_str))

            hora_fin = (datetime.combine(date.today(), hora_inicio) + duracion_td).time()

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
                    vehicle = Vehicle.objects.get(matricula=vehicle_matricula, propietari=request.user)
                except Vehicle.DoesNotExist:
                    return Response({'error': 'Vehicle no trobat'}, status=404)


                vehicle_carregadors = set(vehicle.model_cotxe.tipus_carregador.all().values_list('id_carregador', flat=True))
                estacio_carregadors = set(estacio.tipus_carregador.all().values_list('id_carregador', flat=True))

                if not vehicle_carregadors.intersection(estacio_carregadors):
                    return Response({'error': 'El vehicle no és compatible amb aquesta estació de càrrega'}, status=400)


            reserva = Reserva.objects.create(
                usuario=request.user,
                estacion=estacio,
                fecha=fecha,
                hora=hora_inicio,
                duracion=duracion_td,
                vehicle=vehicle
            )


            return Response({'message': 'Reserva creada amb éxit'}, status=201)

        except EstacioCarrega.DoesNotExist:
            return Response({'error': 'Estació no trobada'}, status=404)

    # @action(detail=True, methods=['put'], permission_classes=[permissions.IsAuthenticated])
    @action(detail=True, methods=['put'])
    def modificar(self, request, pk=None):

        try:
            reserva = get_object_or_404(Reserva, id=pk, usuario=request.user)
        except Reserva.DoesNotExist:
            return Response({'error': 'Reserva no encontrada o sin permiso'}, status=status.HTTP_404_NOT_FOUND)

        # if reserva.vehicle is None or reserva.vehicle.propietari != request.user:
        #     return Response({'error': 'No tens permís per modificar aquesta reserva'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        try:
            fecha_str = data.get('fecha', reserva.fecha.strftime('%d/%m/%Y')); fecha = datetime.strptime(fecha_str, '%d/%m/%Y').date()
            hora_str = data.get('hora', reserva.hora.strftime('%H:%M')); hora_inicio = datetime.strptime(hora_str, '%H:%M').time()
            duracion_str = data.get('duracion', str(reserva.duracion))
            if isinstance(duracion_str, timedelta): duracion_td = duracion_str
            elif ':' in duracion_str: partes = duracion_str.split(':'); horas, minutos = int(partes[0]), int(partes[1]); segundos = int(partes[2]) if len(partes) > 2 else 0; duracion_td = timedelta(hours=horas, minutes=minutos, seconds=segundos)
            else: duracion_td = timedelta(seconds=int(duracion_str))
            vehicle_matricula = data.get('vehicle')
            vehicle = reserva.vehicle

            hora_fin = (datetime.combine(date.min, hora_inicio) + duracion_td).time()
            reservas_existentes = Reserva.objects.filter(estacion=reserva.estacion, fecha=fecha).exclude(id=pk)
            placesReservades = 0
            for reserva_existente in reservas_existentes:
                hora_reserva_fin = (datetime.combine(date.min, reserva_existente.hora) + reserva_existente.duracion).time()
                if not (hora_fin <= reserva_existente.hora or hora_inicio >= hora_reserva_fin):
                    placesReservades += 1
                    try: n_places_disponibles = int(reserva.estacion.nplaces)
                    except(ValueError, TypeError): n_places_disponibles=1
                    if placesReservades >= n_places_disponibles: return Response({'error': 'No hi ha places lliures...'}, status=409)

            if vehicle_matricula is not None:
                if vehicle_matricula == "": vehicle = None
                else:
                    vehicle = get_object_or_404(Vehicle, matricula=vehicle_matricula, propietari=request.user)
                    vehicle_carregadors = set(vehicle.model_cotxe.tipus_carregador.all().values_list('id_carregador', flat=True))
                    estacio_carregadors = set(reserva.estacion.tipus_carregador.all().values_list('id_carregador', flat=True))
                    if not vehicle_carregadors.intersection(estacio_carregadors): return Response({'error': 'Nou vehicle no compatible'}, status=400)
            reserva.fecha = fecha; reserva.hora = hora_inicio; reserva.duracion = duracion_td; reserva.vehicle = vehicle
            reserva.save()

            return Response({'message': 'Reserva actualizada con éxito'}, status=200)

        except Vehicle.DoesNotExist: return Response({'error': 'Vehicle especificat no trobat o no pertany a l\'usuari'}, status=404)
        except (ValueError, TypeError) as e: return Response({'error': f'Error format dades: {e}'}, status=400)
        except Exception as e: print(f"Error modificando reserva {pk}: {e}"); return Response({'error': 'Error intern'}, status=500)


    @action(detail=True, methods=['delete'])
    def eliminar(self, request, pk=None):

        reserva = get_object_or_404(Reserva, id=pk, usuario=request.user)
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
    """Obtiene el precio del kWh para hoy desde la API de REE."""

    hoy = datetime.now().date()
    fecha_str_api = hoy.strftime("%Y-%m-%d")
    fecha_str_display = hoy.strftime("%d/%m/%Y")

    fecha_inicio = f"{fecha_str_api}T00:00"
    fecha_fin = f"{fecha_str_api}T23:59"

    url = (
        "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
        f"?start_date={fecha_inicio}&end_date={fecha_fin}&time_trunc=hour"
    )

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
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
                            precios_kwh_hoy.append({"hora": hora_simple, "precio_kwh": round(precio_kwh, 5)})
                        except (ValueError, TypeError) as e:
                            print(f"Error procesando valor REE {valor_hora}: {e}")
                            continue

        if not precios_kwh_hoy:
            return Response({"error": "No se encontraron datos horarios en la respuesta de la API REE"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "fecha": fecha_str_display,
            "precios_hoy": precios_kwh_hoy,
            "unidad": "€/kWh",
            "fuente": "Red Eléctrica de España (REE)"
        }, status=status.HTTP_200_OK)

    except requests.Timeout:
        return Response({"error": "Timeout conectando con API REE"}, status=status.HTTP_504_GATEWAY_TIMEOUT)
    except requests.HTTPError as e:
        error_detail = f"Error HTTP {e.response.status_code} desde API REE"
        try:
            error_data = e.response.json()
            if "errors" in error_data and error_data["errors"]:
                error_detail = error_data["errors"][0].get("detail", error_detail)
        except (json.JSONDecodeError, AttributeError, IndexError, KeyError):
            pass
        return Response({"error": f"Error al obtener datos de REE: {error_detail}"}, status=e.response.status_code)
    except requests.RequestException as e:
        return Response({"error": f"Fallo conexión con API REE: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        print(f"Error inesperado en obtenir_preu_actual_kwh: {e}")
        return Response({'error': 'Error inesperado en el servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post', 'get'])
    def sumaPunts(self, request, pk=None):
        usuario = self.get_object()
        
        if request.method == 'GET':
            punts = request.query_params.get('punts', 0)
        else:
            punts = request.data.get('punts', 0)
        
        try:
            punts = int(punts)
            nuevos_punts = usuario.sumar_punts(punts)
            
            return Response({
                "message": f"Se han añadido {punts} puntos al usuario",
                "puntos_añadidos": punts,
                "puntos_actuales": nuevos_punts
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post', 'get'])
    def restarPunts(self, request, pk=None):
        usuario = self.get_object()
        
        if request.method == 'GET':
            punts = request.query_params.get('punts', 0)
        else:
            punts = request.data.get('punts', 0)
        
        try:
            punts = int(punts)
            nuevos_punts = usuario.restar_punts(punts)
            
            return Response({
                "message": f"Se han restado {punts} puntos al usuario",
                "puntos_restados": punts,
                "puntos_actuales": nuevos_punts
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def getPunts(self, request, pk=None):
        usuario = self.get_object()
        return Response({
            "usuario_id": usuario.id,
            "nombre": f"{usuario.first_name} {usuario.last_name}",
            "puntos": usuario.punts
        }, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['put'], url_path='update-language')
    def update_language(self, request, pk=None):
        usuario = self.get_object()
        
        idioma = request.data.get('idioma')
        if idioma not in Idiomas.values:
            return Response({"error": "Not valid language"}, status=status.HTTP_400_BAD_REQUEST)
        
        usuario.idioma = idioma
        usuario.save()
        
        return Response({"message": "Language updated successfully", "Language": usuario.idioma})

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Usuario creado correctamente"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)
    
class PerfilPublicoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = PerfilPublicoSerializer
    permission_classes = [AllowAny]  # o IsAuthenticated si quieres solo para usuarios registrados
    lookup_field = 'username'

class PerfilFotoView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get(self, request):
        """Obtener la foto del usuario actual"""
        serializer = FotoPerfilSerializer(request.user)
        return Response(serializer.data)

    def post(self, request):
        """Crear o reemplazar la foto del usuario actual"""
        serializer = FotoPerfilSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        """Eliminar la foto del usuario actual"""
        user = request.user
        user.foto.delete(save=True)
        return Response({'message': 'Foto eliminada correctamente'}, status=204)

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
    

class TextItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TextItem.objects.all()
    serializer_class = TextItemSerializer