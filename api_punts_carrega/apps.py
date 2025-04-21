from django.apps import AppConfig


class ApiPuntsCarregaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_punts_carrega'

    def ready(self):
        from .social_setup import create_social_apps
        try:
            create_social_apps()
        except Exception as e:
            print(f"[SocialApp Init] Aviso: {e}")