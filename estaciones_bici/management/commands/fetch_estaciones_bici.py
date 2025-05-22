from django.core.management.base import BaseCommand
from estaciones_bici.utils import importar_estaciones_bici_desde_api

class Command(BaseCommand):
    help = 'Importa estaciones de bici desde la API externa del Ayuntamiento de Barcelona'

    def handle(self, *args, **kwargs):
        importar_estaciones_bici_desde_api()
        self.stdout.write(self.style.SUCCESS("Estaciones importadas correctamente"))
