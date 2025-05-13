from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import EstacionBici
from .serializers import EstacionBiciSerializer

class EstacionBiciViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EstacionBici.objects.all()
    serializer_class = EstacionBiciSerializer
    permission_classes = [permissions.AllowAny]
