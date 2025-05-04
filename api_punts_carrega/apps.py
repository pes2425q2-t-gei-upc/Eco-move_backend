from django.apps import AppConfig


class ApiPuntsCarregaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_punts_carrega'
    
    def ready(self):
        import api_punts_carrega.translation
