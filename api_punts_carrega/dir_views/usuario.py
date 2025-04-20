from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


from api_punts_carrega.models import Usuario
from api_punts_carrega.serializers import UsuarioSerializer, UsuarioUpdateSerializer, UsuarioCreateSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        return UsuarioSerializer
    
    @action(detail=True, methods=['post', 'get'])
    def sumaPunts(self, request, pk=None):
       
        usuario = self.get_object()
        
        
        if request.method == 'GET':
            punts = request.query_params.get('punts', 0)
        else:
            punts = request.data.get('punts', 0)
        
        try:
            punts = int(punts)
            if punts <= 0:
                return Response(
                    {"error": "La cantidad de puntos debe ser un número positivo"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "La cantidad de puntos debe ser un número entero"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        usuario.punts += punts
        usuario.save()
        
        return Response({
            "message": f"Se han añadido {punts} puntos al usuario",
            "puntos_añadidos": punts,
            "puntos_actuales": usuario.punts
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post', 'get'])
    def restarPunts(self, request, pk=None):
       
        usuario = self.get_object()
        
        
        if request.method == 'GET':
            punts = request.query_params.get('punts', 0)
        else:
            punts = request.data.get('punts', 0)
        
        try:
            punts = int(punts)
            if punts <= 0:
                return Response(
                    {"error": "La cantidad de puntos debe ser un número positivo"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "La cantidad de puntos debe ser un número entero"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si el usuario tiene suficientes puntos
        if usuario.punts < punts:
            return Response(
                {"error": f"El usuario solo tiene {usuario.punts} puntos, no se pueden restar {punts}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        usuario.punts -= punts
        usuario.save()
        
        return Response({
            "message": f"Se han restado {punts} puntos al usuario",
            "puntos_restados": punts,
            "puntos_actuales": usuario.punts
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def getPunts(self, request, pk=None):
        
        usuario = self.get_object()
        return Response({
            "usuario_id": usuario.id,
            "nombre": f"{usuario.first_name} {usuario.last_name}",
            "puntos": usuario.punts
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get', 'put'], permission_classes=[IsAuthenticated])
    def me(self, request):
        usuario = request.user

        if request.method == 'GET':
            serializer = self.get_serializer(usuario)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = UsuarioUpdateSerializer(usuario, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(UsuarioSerializer(usuario).data)