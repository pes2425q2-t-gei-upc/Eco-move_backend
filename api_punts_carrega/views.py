from datetime import date, datetime, timedelta, timezone, time
import json
import math
import requests

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.dateparse import parse_datetime, parse_date, parse_time
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from .serializers import ReservaSerializer

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


class ReservaSerializerr(serializers.ModelSerializer):
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
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        try:
            user = self.request.user
            queryset = Reserva.objects.filter(usuario=user)
        except AttributeError:
            return Reserva.objects.none()

        estacion_id = self.request.query_params.get('estacion_id')
        if estacion_id:
            queryset = queryset.filter(estacion__id_punt=estacion_id)

        dia_str = self.request.query_params.get('dia')
        if dia_str:
            dia = parse_date(dia_str)
            if dia:
                start_of_day = timezone.make_aware(datetime.combine(dia, time.min))
                end_of_day = timezone.make_aware(datetime.combine(dia, time.max))
                queryset = queryset.filter(
                    hora_inicio__lt=end_of_day + timedelta(microseconds=1),
                    hora_fin__gt=start_of_day - timedelta(microseconds=1)
                )
                return queryset.select_related('usuario', 'estacion')

        overlaps_start_str = self.request.query_params.get('overlaps_start')
        overlaps_end_str = self.request.query_params.get('overlaps_end')
        if overlaps_start_str and overlaps_end_str:
            overlaps_start = parse_datetime(overlaps_start_str)
            overlaps_end = parse_datetime(overlaps_end_str)
            if overlaps_start and overlaps_end and overlaps_end > overlaps_start:
                queryset = queryset.filter(
                    hora_inicio__lt=overlaps_end, hora_fin__gt=overlaps_start
                )

        return queryset.select_related('usuario', 'estacion')


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error en create estándar: {e}")
            return Response({"error": "Error interno al procesar la petición"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def crear(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Autenticación requerida'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({'error': 'JSON inválido'}, status=status.HTTP_400_BAD_REQUEST)

        estacio_id = data.get('estacion')
        fecha_str = data.get('fecha')
        hora_str = data.get('hora')
        duracion_str = data.get('duracion')

        if not all([estacio_id, fecha_str, hora_str, duracion_str]):
            return Response({'error': 'Faltan datos'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            estacio = get_object_or_404(EstacioCarrega, id_punt=estacio_id)
            fecha = datetime.strptime(fecha_str, '%d/%m/%Y').date()
            hora_inicio_time = datetime.strptime(hora_str, '%H:%M').time()

            if ':' in duracion_str:
                partes = duracion_str.split(':')
                horas = int(partes[0])
                minutos = int(partes[1])
                segundos = int(partes[2]) if len(partes) > 2 else 0
                duracion_td = timedelta(hours=horas, minutes=minutos, seconds=segundos)
            else:
                duracion_td = timedelta(seconds=int(duracion_str))

            hora_inicio_dt = timezone.make_aware(datetime.combine(fecha, hora_inicio_time))
            hora_fin_dt = hora_inicio_dt + duracion_td

            reservas_existentes = Reserva.objects.filter(estacion=estacio, hora_inicio__lt=hora_fin_dt, hora_fin__gt=hora_inicio_dt)

            try:
                n_places_disponibles = int(estacio.nplaces)
            except (ValueError, TypeError):
                print(f"WARN: nplaces no es numérico para estación {estacio.id_punt}. Usando 1 por defecto.")
                n_places_disponibles = 1

            if reservas_existentes.count() >= n_places_disponibles:
                return Response({'error': 'No hi ha places lliures...'}, status=status.HTTP_409_CONFLICT)

            reserva = Reserva.objects.create(
                usuario=request.user,
                estacion=estacio,
                hora_inicio=hora_inicio_dt,
                hora_fin=hora_fin_dt
            )

            serializer_response = self.get_serializer(reserva)
            return Response(serializer_response.data, status=status.HTTP_201_CREATED)

        except EstacioCarrega.DoesNotExist:
            return Response({'error': 'Estació no trobada'}, status=status.HTTP_404_NOT_FOUND)
        except (ValueError, TypeError) as e:
            return Response({'error': f'Error formato datos: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error creando reserva (acción): {e}")
            return Response({'error': 'Error intern'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['put'], permission_classes=[permissions.IsAuthenticated])
    def modificar(self, request, pk=None):
        try:
            reserva = get_object_or_404(Reserva, id=pk, usuario=request.user)
        except Reserva.DoesNotExist:
            return Response({'error': 'Reserva no encontrada o sin permiso'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data

        try:
            # Parsear datos (usando parse_date/parse_time para flexibilidad)
            fecha_str = data.get('fecha', reserva.hora_inicio.strftime('%Y-%m-%d'))
            fecha = parse_date(fecha_str)
            if fecha is None: raise ValueError(f"Formato de fecha inválido: '{fecha_str}'")

            hora_str = data.get('hora', reserva.hora_inicio.strftime('%H:%M'))
            hora_inicio_time = parse_time(hora_str)
            if hora_inicio_time is None: raise ValueError(f"Formato de hora inválido: '{hora_str}'")

            # Parsear duración (tu lógica)
            current_duration = reserva.duracion
            duracion_str = data.get('duracion', str(current_duration) if current_duration else None)
            if duracion_str is None: return Response({'error': 'Falta la duración'}, status=status.HTTP_400_BAD_REQUEST)
            if isinstance(duracion_str, timedelta): duracion_td = duracion_str
            elif ':' in duracion_str: partes = duracion_str.split(':'); horas, minutos = int(partes[0]), int(partes[1]); segundos = int(partes[2]) if len(partes) > 2 else 0; duracion_td = timedelta(hours=horas, minutes=minutos, seconds=segundos)
            else: duracion_td = timedelta(seconds=int(duracion_str))

            # --- Recalcular DateTime de inicio y fin (Usando django.utils.timezone) ---
            naive_datetime = datetime.combine(fecha, hora_inicio_time)
            hora_inicio_dt = timezone.make_aware(naive_datetime) # <--- CORREGIDO
            hora_fin_dt = hora_inicio_dt + duracion_td

            # ... (resto de la validación de solapamiento y guardado) ...
            reservas_existentes = Reserva.objects.filter(estacion=reserva.estacion, hora_inicio__lt=hora_fin_dt, hora_fin__gt=hora_inicio_dt).exclude(id=pk)
            try: n_places_disponibles = int(reserva.estacion.nplaces)
            except(ValueError, TypeError): n_places_disponibles=1
            if reservas_existentes.count() >= n_places_disponibles: return Response({'error': 'No hi ha places lliures...'}, status=status.HTTP_409_CONFLICT)
            reserva.hora_inicio = hora_inicio_dt; reserva.hora_fin = hora_fin_dt; reserva.save()
            serializer = self.get_serializer(reserva)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except (ValueError, TypeError) as e:
            return Response({'error': f'Error en formato de datos: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error modificando reserva {pk}: {e}")
            return Response({'error': 'Error intern servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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