from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import EstacionBici
from .serializers import EstacionBiciSerializer, EstacionBiciLiteSerializer
from .utils import importar_estaciones_bici_desde_api, actualizar_disponibilidad_estaciones
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


class EstacionBiciViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EstacionBici.objects.all()
    serializer_class = EstacionBiciSerializer
    permission_classes = [permissions.AllowAny]

class EstacionBiciLiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EstacionBici.objects.all()
    serializer_class = EstacionBiciLiteSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            from .serializers import EstacionBiciDetalleSerializer
            return EstacionBiciDetalleSerializer
        from .serializers import EstacionBiciLiteSerializer
        return EstacionBiciLiteSerializer
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def forzar_importar_estaciones(request):
    importar_estaciones_bici_desde_api()
    return Response({"message": "Importación completada correctamente."})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def forzar_actualizar_disponibilidad(request):
    actualizar_disponibilidad_estaciones()
    return Response({"message": "Disponibilidad actualizada correctamente."})