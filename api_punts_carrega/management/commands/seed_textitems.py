from django.core.management.base import BaseCommand
from api_punts_carrega.models import TextItem

class Command(BaseCommand):
    help = "Seed initial TextItems for translations"

    def handle(self, *args, **kwargs):
        items = [
            {
                "key": "welcome_message",
                "text_ca": "Benvingut a l'aplicació!",
                "text_en": "Welcome to the app!",
                "text_es": "¡Bienvenido a la aplicación!",
            },
            {
                "key": "change_language",
                "text_ca": "Canvia l'idioma",
                "text_en": "Change language",
                "text_es": "Cambiar idioma",
            },
            {
                "key": "save",
                "text_ca": "Desa",
                "text_en": "Save",
                "text_es": "Guardar",
            },
        ]

        for item in items:
            obj, created = TextItem.objects.get_or_create(key=item["key"])
            obj.text_ca = item["text_ca"]
            obj.text_en = item["text_en"]
            obj.text_es = item["text_es"]
            obj.save()

        self.stdout.write(self.style.SUCCESS("Seeded initial TextItems"))
