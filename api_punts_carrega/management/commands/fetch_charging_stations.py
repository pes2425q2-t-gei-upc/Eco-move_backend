import requests
from api_punts_carrega.models import ChargingStation
from django.core.management.base import BaseCommand

API_url = "https://analisi.transparenciacatalunya.cat/resource/tb2m-m33b.json"

class Command(BaseCommand):
    help = "Fetch and store charging station data from the external API"
    
    def handle(self, *args, **kwargs):
        response = requests.get(API_url)
        if response.status_code == 200:
            data = response.json()
            ChargingStation.objects.all().delete() #clear the old data
            for station in data:
                ChargingStation.objects.create(
                    id_station = station.get("id", "Unknown"), # Sets it to unknown if there is no data there
                    description_location=station.get("designaci_descriptiva", "Unknown"),
                    address=station.get("adre_a", "No address available"),
                    city=station.get("municipi", "Unknown"),
                    province=station.get("provincia", "Unknown"),
                    power_kw=station.get("kw"),
                    speed_type=station.get("tipus_velocitat", "Unknown"),
                    vehicle_type=station.get("tipus_vehicle", "Unknown"),
                    current_type=station.get("ac_dc", "Unknown"),
                    connection_type=station.get("tipus_connexi", "Unknown"),
                    num_spots=station.get("nplaces_estaci", "Unknown"),
                    access_type=station.get("acces", "Unknown"),
                    operator=station.get("promotor_gestor", "Unknown"),
                    latitude=float(station["latitud"]) if "latitud" in station else None,
                    longtitude=float(station["longitud"]) if "longitud" in station else None,
                )
            self.stdout.write(self.style.SUCCESS("Charging stations updated successfully"))
        else:
            self.stderr.write("Failed to fetch data from API")

        