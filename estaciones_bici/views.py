from django.shortcuts import render
from rest_framework import viewsets, permissions, status, serializers
from .models import EstacionBici, DisponibilidadEstacionBici, ReservaBici
from .serializers import EstacionBiciSerializer, EstacionBiciLiteSerializer, ReservaBiciSerializer
from .utils import importar_estaciones_bici_desde_api, actualizar_disponibilidad_estaciones
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import now, timedelta
from rest_framework.viewsets import ModelViewSet

RESERVA_BICI_MINUTOS = 15

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

class ReservaBiciViewSet(ModelViewSet):
    queryset = ReservaBici.objects.all()
    serializer_class = ReservaBiciSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReservaBici.objects.filter(usuario=self.request.user, activa=True)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        estacion = serializer.validated_data["estacion"]
        tipo = serializer.validated_data["tipo_bicicleta"]

        # Obtener disponibilidad real
        try:
            disponibilidad = estacion.estado
        except:
            raise serializers.ValidationError("No hay datos de disponibilidad.")

        # Limpiar reservas expiradas
        ReservaBici.objects.filter(activa=True, expiracion__lt=now()).update(activa=False)

        reservas_activas = ReservaBici.objects.filter(
            estacion=estacion,
            tipo_bicicleta=tipo,
            activa=True,
            expiracion__gt=now()
        ).count()

        disponibles = (
            disponibilidad.num_bicis_mecanicas if tipo == 'mecanica'
            else disponibilidad.num_bicis_electricas
        )

        if reservas_activas >= disponibles:
            raise serializers.ValidationError("No hay bicicletas disponibles para reservar.")

        reserva = serializer.save(
            usuario=request.user,
            expiracion=now() + timedelta(minutes=RESERVA_BICI_MINUTOS),
            activa=True
        )

        response_serializer = self.get_serializer(reserva)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=['get'])
    def mis_reservas(self, request):
        reservas = self.get_queryset()
        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        reserva = self.get_object()

        if reserva.usuario != request.user:
            return Response(
                {"detail": "No puedes cancelar reservas de otros usuarios."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not reserva.activa:
            return Response(
                {"detail": "La reserva ya no está activa."},
                status=status.HTTP_400_BAD_REQUEST
            )

        reserva.activa = False
        reserva.save()
        return Response(
            {"detail": "Reserva cancelada correctamente."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def historial(self, request):
        reservas = ReservaBici.objects.filter(usuario=request.user, activa=False)
        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)