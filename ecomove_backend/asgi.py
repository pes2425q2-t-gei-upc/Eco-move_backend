"""
ASGI config for ecomove_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import social_community.routing  # Vamos a crear este archivo

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecomove_backend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            social_community.routing.websocket_urlpatterns
        )
    ),
})