from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AlertsViewSet,
    ChatViewSet,
    MessageViewSet,
    ReportViewSet,
)

router = DefaultRouter()
router.register(r'alerts', AlertsViewSet, basename='alerts')
router.register(r'chat', ChatViewSet, basename='chat')
router.register(r'messages', MessageViewSet, basename='messages')
router.register(r'reports',ReportViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
]