from datetime import datetime
import requests
import os
from django.utils.timezone import make_aware, now
from .models import EstacionBici, DisponibilidadEstacionBici, UltimaActualizacionBicing

def get_bicing_headers() -> dict:
    token = os.environ.get("Token_openData")
    if not token:
        raise EnvironmentError("Falta la variable de entorno Token_openData")

    return {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

def importar_estaciones_bici_desde_api():
    url = os.environ.get("BICING_API_INFO_URL")

    headers = get_bicing_headers()

    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()

    json_data = response.json()
    last_updated = json_data.get("last_updated")  # <-- si la API lo da
    estaciones = json_data["data"]["stations"]

    for est in estaciones:
        EstacionBici.objects.update_or_create(
            station_id=est["station_id"],
            defaults={
                "name": est["name"],
                "address": est["address"],
                "post_code": est.get("post_code"),
                "lat": est["lat"],
                "lon": est["lon"],
                "capacity": est["capacity"],
                "is_charging_station": est["is_charging_station"],
            }
        )

    UltimaActualizacionBicing.objects.update_or_create(
        tipo="informacion",
        defaults={
            "fecha_llamada": now(),
            "fecha_actualizacion_api": make_aware(datetime.fromtimestamp(last_updated)) if last_updated else now()
        }
    )

def actualizar_disponibilidad_estaciones():
    url = os.environ.get("BICING_API_REALTIME_URL")
    
    headers = get_bicing_headers()

    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()

    json_data = response.json()
    last_updated = json_data["last_updated"]
    estaciones = json_data["data"]["stations"]

    estaciones_bd = {e.station_id: e for e in EstacionBici.objects.all()}
    for est in estaciones:
        try:
            estacion = estaciones_bd.get(est["station_id"])
            if not estacion:
                continue
            DisponibilidadEstacionBici.objects.update_or_create(
                estacion=estacion,
                defaults={
                    "num_bicis_disponibles": est["num_bikes_available"],
                    "num_bicis_mecanicas": est["num_bikes_available_types"].get("mechanical", 0),
                    "num_bicis_electricas": est["num_bikes_available_types"].get("ebike", 0),
                    "num_docks_disponibles": est["num_docks_available"],
                    "estado": est["status"]
                }
            )
        except EstacionBici.DoesNotExist:
            continue

    UltimaActualizacionBicing.objects.update_or_create(
        tipo="disponibilidad",
        defaults={
            "fecha_llamada": now(),
            "fecha_actualizacion_api": make_aware(datetime.fromtimestamp(last_updated))
        }
    )