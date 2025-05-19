from django.core.management.base import BaseCommand
from estaciones_bici.utils import actualizar_disponibilidad_estaciones

class Command(BaseCommand):
    help = 'Actualiza la disponibilidad en tiempo real de las estaciones de bicicletas'

    def handle(self, *args, **kwargs):
        try:
            actualizar_disponibilidad_estaciones()
            self.stdout.write(self.style.SUCCESS('Disponibilidad actualizada correctamente'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error al actualizar: {e}'))
