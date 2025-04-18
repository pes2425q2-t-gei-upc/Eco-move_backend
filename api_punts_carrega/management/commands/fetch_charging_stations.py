import requests, random
from api_punts_carrega.models import EstacioCarrega, TipusCarregador, TipusVelocitat, Punt
from django.db import transaction
from django.core.management.base import BaseCommand

API_url = "https://analisi.transparenciacatalunya.cat/resource/tb2m-m33b.json"

class Command(BaseCommand):
    help = "Fetch and store charging station data from the external API"
    
    def handle(self, *args, **kwargs):
        response = requests.get(API_url)
        if response.status_code == 200:
            data = response.json()
            total_stations = len(data)
            self.stdout.write(f"Total stations to process: {total_stations}")
            
            # Limpiar datos existentes
            EstacioCarrega.objects.all().delete()
            TipusCarregador.objects.all().delete()
            TipusVelocitat.objects.all().delete()
            Punt.objects.all().delete()
            
            with transaction.atomic():
                for index, station in enumerate(data):
                    lat = float(station.get("latitud", 0))
                    lng = float(station.get("longitud", 0))
                    num_get = station.get("nplaces_estaci","Unknown")
                    if num_get == "" or num_get == "Unknown":
                        num_places = str(random.randint(1,10))
                    else:
                        num_places = num_get
                    
                    # Crear la estación de carga (sin tipus_velocitat por ahora)
                    estacio_carrega = EstacioCarrega.objects.create(
                        id_punt = station.get("id", "Unknown"),
                        lat = lat,
                        lng = lng,
                        direccio = station.get("adre_a", "No address available"),
                        ciutat = station.get("municipi", "Unknown"),
                        provincia = station.get("provincia", "Unknown"),
                        gestio = station.get("promotor_gestor", "Unknown"),
                        tipus_acces = station.get("acces", "Unknown"),
                        nplaces = num_places,
                        potencia = station.get("kw","Unknown"),
                        # Ya no incluimos tipus_velocitat aquí porque ahora es una relación M2M
                    )
                    
                    # Procesar y guardar los tipos de velocidad
                    tipus_velocitat_raw = station.get("tipus_velocitat", "Unknown")
                    
                    # Comprobar si hay múltiples tipos de velocidad (separados por " i ")
                    if " i " in tipus_velocitat_raw:
                        velocitats = [v.strip() for v in tipus_velocitat_raw.split(" i ")]
                        for velocitat in velocitats:
                            # Crear o obtener el tipo de velocidad
                            tipus_velocitat, created = TipusVelocitat.objects.get_or_create(
                                id_velocitat = velocitat,
                                defaults={
                                    'nom_velocitat': velocitat,
                                }
                            )
                            # Asociar a la estación
                            estacio_carrega.tipus_velocitat.add(tipus_velocitat)
                    else:
                        # Caso de un solo tipo de velocidad
                        tipus_velocitat, created = TipusVelocitat.objects.get_or_create(
                            id_velocitat = tipus_velocitat_raw,
                            defaults={
                                'nom_velocitat': tipus_velocitat_raw,
                            }
                        )
                        estacio_carrega.tipus_velocitat.add(tipus_velocitat)
                    
                    # Procesar tipos de cargadores (separar valores múltiples)
                    tipus_connexi_raw = station.get("tipus_connexi", "Unknown")
                    ac_dc = station.get("ac_dc", "Unknown")
                    
                    # Si hay múltiples tipos de conexión (separados por +)
                    if "+" in tipus_connexi_raw:
                        connectors = [c.strip() for c in tipus_connexi_raw.split("+")]
                        for connector in connectors:
                            tipus_carregador, created = TipusCarregador.objects.get_or_create(
                                id_carregador = f"{connector} {ac_dc}",
                                defaults={
                                    'nom_tipus': connector,
                                    'tipus_connector': connector,
                                    'tipus_corrent': ac_dc,
                                }
                            )
                            estacio_carrega.tipus_carregador.add(tipus_carregador)
                    else:
                        # Caso de un solo tipo de conector
                        tipus_carregador, created = TipusCarregador.objects.get_or_create(
                            id_carregador = f"{tipus_connexi_raw} {ac_dc}",
                            defaults={
                                'nom_tipus': tipus_connexi_raw,
                                'tipus_connector': tipus_connexi_raw,
                                'tipus_corrent': ac_dc,
                            }
                        )
                        estacio_carrega.tipus_carregador.add(tipus_carregador)

                    progress = (index + 1) / total_stations * 100
                    self.stdout.write(f"\rProcessing station {index + 1}/{total_stations} ({progress:.2f}%)", ending="")
                
                self.stdout.write(self.style.SUCCESS("Charging stations updated successfully"))
        else:
            self.stderr.write("Failed to fetch data from API")