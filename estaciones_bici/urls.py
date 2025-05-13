from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EstacionBiciViewSet

router = DefaultRouter()
router.register(r'estaciones', EstacionBiciViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
