# estaciones_bici/utils.py
import requests
import os
from .models import EstacionBici

def importar_estaciones_bici_desde_api():
    url = "https://opendata-ajuntament.barcelona.cat/data/dataset/bd2462df-6e1e-4e37-8205-a4b8e7313b84/resource/f60e9291-5aaa-417d-9b91-612a9de800aa/download"
    
    bicing_api_token = os.environ.get("Token_openData")
    
    headers = {
        "Authorization": bicing_api_token,
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    estaciones = response.json()["data"]["stations"]

    for est in estaciones:
        EstacionBici.objects.update_or_create(
            station_id=est["station_id"],
            defaults={
                "name": est["name"],
                "address": est["address"],
                "cross_street": est.get("cross_street"),
                "post_code": est.get("post_code"),
                "lat": est["lat"],
                "lon": est["lon"],
                "altitude": est.get("altitude"),
                "capacity": est["capacity"],
                "is_charging_station": est["is_charging_station"],
                "ride_code_support": est.get("_ride_code_support", False),
                "nearby_distance": est.get("nearby_distance"),
                "physical_configuration": est.get("physical_configuration"),
            }
        )
