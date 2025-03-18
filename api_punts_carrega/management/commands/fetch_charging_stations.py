import requests
from api_punts_carrega.models import Ubicacio, EstacioCarrega, PuntCarrega, TipusCarregador, Punt
from django.db import transaction
from django.core.management.base import BaseCommand

API_url = "https://analisi.transparenciacatalunya.cat/resource/tb2m-m33b.json"

class Command(BaseCommand):
    help = "Fetch and store charging station data from the external API"
    
    def handle(self, *args, **kwargs):
        response = requests.get(API_url)
        if response.status_code == 200:
            data = response.json()
            Ubicacio.objects.all().delete()
            EstacioCarrega.objects.all().delete()
            PuntCarrega.objects.all().delete()
            TipusCarregador.objects.all().delete()
            Punt.objects.all().delete()
            with transaction.atomic():
                for station in data:
                    lat = float(station.get("latitud", 0))
                    lng = float(station.get("longitud", 0))
                    ubicacio, created = Ubicacio.objects.get_or_create(
                        lat = lat,
                        lng = lng,
                        defaults={
                            'id_ubicacio' : station.get("id", "Unknown"),
                            'direccio' : station.get("adre_a", "No address available"),
                            'ciutat' : station.get("municipi", "Unknown"),
                            'provincia' : station.get("provincia", "Unknown"),
                        }
                    )

                    ubicacio.save()

                    Punt.objects.create(
                        id_punt = station.get("id", "Unknown"),
                        ubicacio_punt = ubicacio,
                    )
                    
                    estacio_carrega = EstacioCarrega.objects.create(
                        id_estacio = station.get("id", "Unknown"),
                        gestio = station.get("promotor_gestor", "Unknown"),
                        tipus_acces = station.get("acces", "Unknown"),
                        ubicacio_estacio = ubicacio,
                        nplaces = station.get("nplaces_estaci", "Unknown"),
                    )

                    PuntCarrega.objects.create(
                        id_punt_carrega = station.get("id", "Unknown"),
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

                    punt_carrega_obj = PuntCarrega.objects.get(id_punt_carrega=station.get("id", "Unknown"))

                    tipus_carregador.punt_carrega.set([punt_carrega_obj])
                self.stdout.write(self.style.SUCCESS("Charging stations updated successfully"))
        else:
            self.stderr.write("Failed to fetch data from API")

        