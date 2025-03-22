import requests
from api_punts_carrega.models import EstacioCarrega, PuntCarrega, TipusCarregador, Punt
from django.db import transaction
from django.core.management.base import BaseCommand

API_url = "https://analisi.transparenciacatalunya.cat/resource/tb2m-m33b.json"

class Command(BaseCommand):
    help = "Fetch and store charging station data from the external API"
    
    def handle(self, *args, **kwargs):
        response = requests.get(API_url)
        if response.status_code == 200:
            data = response.json()
            total_stations = len(data)  # Total de estaciones de carga a procesar
            self.stdout.write(f"Total stations to process: {total_stations}")
            EstacioCarrega.objects.all().delete()
            PuntCarrega.objects.all().delete()
            TipusCarregador.objects.all().delete()
            Punt.objects.all().delete()
            num = 0
            with transaction.atomic():
                for index, station in enumerate(data):
                    lat = float(station.get("latitud", 0))
                    lng = float(station.get("longitud", 0))
                    

                    estacio_carrega = EstacioCarrega.objects.create(
                        id_punt = station.get("id", "Unknown"),
                        lat = lat,
                        lng = lng,
                        direccio = station.get("adre_a", "No address available"),
                        ciutat = station.get("municipi", "Unknown"),
                        provincia = station.get("provincia", "Unknown"),
                        gestio = station.get("promotor_gestor", "Unknown"),
                        tipus_acces = station.get("acces", "Unknown"),
                        nplaces = station.get("nplaces_estaci", "Unknown"),
                    )

                    PuntCarrega.objects.create(
                        id_punt_carrega = str(num),
                        potencia = station.get("kw", 0),
                        tipus_velocitat = station.get("tipus_velocitat", "Unknown"),
                        estacio = estacio_carrega,
                    )

                    tipus_carregador, created = TipusCarregador.objects.get_or_create(
                        id_carregador = station.get("tipus_connexi", "Unknown") + "  " + station.get("ac_dc", "Unknown"),
                        defaults={
                            'nom_tipus': station.get("tipus_connexi", "Unknown"),
                            'tipus_connector': station.get("tipus_connexi", "Unknown"),
                            'tipus_corrent': station.get("ac_dc", "Unknown"),
                        }
                    )

                    punt_carrega_obj = PuntCarrega.objects.get(id_punt_carrega = str(num))
                    tipus_carregador.punt_carrega.set([punt_carrega_obj])
                    num += 1
                    progress = (index + 1) / total_stations * 100
                    self.stdout.write(f"\rProcessing station {index + 1}/{total_stations} ({progress:.2f}%)", ending="")
                
                self.stdout.write(self.style.SUCCESS("Charging stations updated successfully"))
        else:
            self.stderr.write("Failed to fetch data from API")