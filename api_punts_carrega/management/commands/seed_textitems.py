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
            {
                "key": "trophy_bronze_name",
                "text_ca": "Trofeu Bronze",
                "text_en": "Bronze Trophy",
                "text_es": "Trofeo Bronce",
            },
            {
                "key": "trophy_bronze_description",
                "text_ca": "Has assolit 50 punts. Bon inici!",
                "text_en": "You have reached 50 points. Good start!",
                "text_es": "Has alcanzado 50 puntos. Buen comienzo!",
            },
            {
                "key": "trophy_silver_name",
                "text_ca": "Trofeu Plata",
                "text_en": "Silver Trophy",
                "text_es": "Trofeo Plata",
            },
            {
                "key": "trophy_silver_description",
                "text_ca": "Has assolit 150 punts. Continua aixi!",
                "text_en": "You have reached 150 points. Keep it up!",
                "text_es": "Has alcanzado 150 puntos. Sigue asi!",
            },
            {
                "key": "trophy_gold_name",
                "text_ca": "Trofeu Or",
                "text_en": "Gold Trophy",
                "text_es": "Trofeo Oro",
            },
            {
                "key": "trophy_gold_description",
                "text_ca": "Has assolit 300 punts. Impressionant!",
                "text_en": "You have reached 300 points. Impressive!",
                "text_es": "Has alcanzado 300 puntos. Impresionante!",
            },
            {
                "key": "trophy_platinum_name",
                "text_ca": "Trofeu Plati",
                "text_en": "Platinum Trophy",
                "text_es": "Trofeo Platino",
            },
            {
                "key": "trophy_platinum_description",
                "text_ca": "Has assolit 500 punts. Ets un expert!",
                "text_en": "You have reached 500 points. You are an expert!",
                "text_es": "Has alcanzado 500 puntos. Eres un experto!",
            },
        ]

        for item in items:
            obj, _ = TextItem.objects.get_or_create(key=item["key"])
            obj.text_ca = item["text_ca"]
            obj.text_en = item["text_en"]
            obj.text_es = item["text_es"]
            obj.save()

        self.stdout.write(self.style.SUCCESS("Seeded initial TextItems"))
