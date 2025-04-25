import requests, random, re
from api_punts_carrega.models import EstacioCarrega, TipusCarregador, TipusVelocitat, Punt
from django.db import transaction
from django.core.management.base import BaseCommand

API_url = "https://analisi.transparenciacatalunya.cat/resource/tb2m-m33b.json"

class Command(BaseCommand):
    help = "Fetch and store charging station data from the external API"
    
    def split_multiple_values(self, text):
        """
        Función para dividir texto que puede contener múltiples valores
        separados por diferentes delimitadores: '+', ',', ' i '
        """
        if not text or text == "Unknown":
            return ["Unknown"]
            
        # Primero reemplazamos todos los separadores por un separador común
        normalized = text.replace(" i ", "|||").replace("+", "|||").replace(",", "|||")
        
        # Dividimos por el separador común y limpiamos espacios
        values = [value.strip() for value in normalized.split("|||") if value.strip()]
        
        return values if values else ["Unknown"]
    
    def normalize_case(self, text):
        """
        Normaliza la capitalización del texto.
        Convierte la primera letra de cada palabra a mayúscula y el resto a minúscula.
        """
        if not text or text == "Unknown":
            return "Unknown"
        
        # Title case: primera letra de cada palabra en mayúscula, resto en minúscula
        return text.title()
    
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
            
            stations_added = 0
            stations_skipped = 0
            
            with transaction.atomic():
                for index, station in enumerate(data):
                    # Check if connection type is empty or unknown
                    tipus_connexi_raw = station.get("tipus_connexi", "Unknown")
                    potencia_raw = station.get("kw", "Unknown")
                    if not tipus_connexi_raw or tipus_connexi_raw == "Unknown" or tipus_connexi_raw == "" or potencia_raw == "0":
                        stations_skipped += 1
                        progress = (index + 1) / total_stations * 100
                        self.stdout.write(f"\rProcessing station {index + 1}/{total_stations} ({progress:.2f}%) - Skipped: {stations_skipped}", ending="")
                        continue  # Skip this station entirely
                    
                    lat = float(station.get("latitud", 0))
                    lng = float(station.get("longitud", 0))
                    num_get = station.get("nplaces_estaci","Unknown")
                    if num_get == "" or num_get == "Unknown":
                        num_places = str(random.randint(1,10))
                    else:
                        num_places = num_get
                    
                    # Crear la estación de carga
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
                    )
                    
                    # Procesar y guardar los tipos de velocidad
                    tipus_velocitat_raw = station.get("tipus_velocitat", "Unknown")
                    velocitats_raw = self.split_multiple_values(tipus_velocitat_raw)
                    
                    # Normalizar cada valor de velocidad
                    velocitats = [self.normalize_case(v) for v in velocitats_raw]
                    
                    # Filter out empty or "Unknown" velocitats
                    valid_velocitats = [velocitat for velocitat in velocitats if velocitat and velocitat != "Unknown" and velocitat != ""]
                    
                    for velocitat in valid_velocitats:
                        tipus_velocitat, created = TipusVelocitat.objects.get_or_create(
                            id_velocitat = velocitat,
                            defaults={
                                'nom_velocitat': velocitat,
                            }
                        )
                        estacio_carrega.tipus_velocitat.add(tipus_velocitat)
                    
                    # Procesar tipos de cargadores con múltiples separadores
                    ac_dc = station.get("ac_dc", "Unknown")
                    
                    connectors_raw = self.split_multiple_values(tipus_connexi_raw)
                    
                    # Normalizar cada tipo de conector
                    connectors = [self.normalize_case(c) for c in connectors_raw]
                    
                    # Filter out empty or "Unknown" connectors
                    valid_connectors = [connector for connector in connectors if connector and connector != "Unknown" and connector != ""]
                    
                    for connector in valid_connectors:
                        tipus_carregador, created = TipusCarregador.objects.get_or_create(
                            id_carregador = f"{connector} {ac_dc}",
                            defaults={
                                'nom_tipus': connector,
                                'tipus_connector': connector,
                                'tipus_corrent': ac_dc,
                            }
                        )
                        estacio_carrega.tipus_carregador.add(tipus_carregador)

                    stations_added += 1
                    progress = (index + 1) / total_stations * 100
                    self.stdout.write(f"\rProcessing station {index + 1}/{total_stations} ({progress:.2f}%) - Added: {stations_added}, Skipped: {stations_skipped}", ending="")
                
                self.stdout.write(self.style.SUCCESS(f"\nCharging stations updated successfully. Added: {stations_added}, Skipped: {stations_skipped}"))
        else:
            self.stderr.write("Failed to fetch data from API")