from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
import requests
import json

from .models import (
    EstacioCarrega, Reserva, Vehicle, Usuario, RefugioClimatico, ValoracionEstacion
)

@staff_member_required
def admin_dashboard(request):
    # Estadísticas generales
    total_estaciones = EstacioCarrega.objects.count()
    total_reservas = Reserva.objects.count()
    total_vehiculos = Vehicle.objects.count()
    total_usuarios = Usuario.objects.count()
    
    # Reservas recientes
    reservas_recientes = Reserva.objects.select_related('estacion', 'vehicle').order_by('-fecha', '-hora')[:10]
    
    # Estaciones más reservadas
    estaciones_populares = Reserva.objects.values('estacion__id_punt').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    estaciones_ids = [item['estacion__id_punt'] for item in estaciones_populares]
    estaciones_populares_data = []
    
    for estacion_id in estaciones_ids:
        try:
            estacion = EstacioCarrega.objects.get(id_punt=estacion_id)
            reservas = Reserva.objects.filter(estacion=estacion).count()
            estaciones_populares_data.append({
                'estacion': estacion,
                'reservas': reservas
            })
        except EstacioCarrega.DoesNotExist:
            continue
    
    # Valoraciones recientes
    valoraciones_recientes = ValoracionEstacion.objects.select_related('estacion', 'usuario').order_by('-fecha_creacion')[:5]
    
    context = {
        'total_estaciones': total_estaciones,
        'total_reservas': total_reservas,
        'total_vehiculos': total_vehiculos,
        'total_usuarios': total_usuarios,
        'reservas_recientes': reservas_recientes,
        'estaciones_populares': estaciones_populares_data,
        'valoraciones_recientes': valoraciones_recientes,
    }
    
    return render(request, 'admin/dashboard.html', context)

@staff_member_required
def sincronizar_refugios_admin(request):
    if request.method == 'POST':
        try:
            response = requests.get('http://nattech.fib.upc.edu:40430/api/refugios/listar/', timeout=10)
            response.raise_for_status()
            
            refugios_data = response.json()
            contador_nuevos = 0
            contador_actualizados = 0
            
            for refugio_data in refugios_data:
                refugio_id = refugio_data['id']
                
                refugio, created = RefugioClimatico.objects.update_or_create(
                    id_punt=refugio_id,
                    defaults={
                        'nombre': refugio_data['nombre'],
                        'lat': float(refugio_data['latitud']),
                        'lng': float(refugio_data['longitud']),
                        'direccio': refugio_data['direccion'],
                        'numero_calle': refugio_data['numero_calle'],
                    }
                )
                
                if created:
                    contador_nuevos += 1
                else:
                    contador_actualizados += 1
            
            messages.success(
                request, 
                f'Sincronización completada. {contador_nuevos} refugios nuevos, {contador_actualizados} actualizados.'
            )
            
        except Exception as e:
            messages.error(request, f'Error al sincronizar refugios: {str(e)}')
        
        return redirect('admin_refugios')
    
    refugios = RefugioClimatico.objects.all().order_by('nombre')
    
    context = {
        'refugios': refugios,
    }
    
    return render(request, 'admin/sincronizar_refugios.html', context)

@staff_member_required
def gestionar_usuarios(request):
    usuarios = Usuario.objects.all().order_by('username')
    
    context = {
        'usuarios': usuarios,
    }
    
    return render(request, 'admin/gestionar_usuarios.html', context)

@staff_member_required
def modificar_puntos_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        puntos = request.POST.get('puntos')
        
        try:
            puntos = int(puntos)
            if puntos <= 0:
                raise ValueError("Los puntos deben ser un número positivo")
                
            if accion == 'sumar':
                usuario.sumar_punts(puntos)
                messages.success(request, f'Se han sumado {puntos} puntos a {usuario.username}')
            elif accion == 'restar':
                usuario.restar_punts(puntos)
                messages.success(request, f'Se han restado {puntos} puntos a {usuario.username}')
            
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('gestionar_usuarios')
    
    context = {
        'usuario': usuario,
    }
    
    return render(request, 'admin/modificar_puntos.html', context)

@staff_member_required
def estadisticas_estaciones(request):
    # Estaciones con más reservas
    estaciones_con_reservas = Reserva.objects.values('estacion__id_punt').annotate(
        total_reservas=Count('id')
    ).order_by('-total_reservas')[:10]
    
    estaciones_ids = [item['estacion__id_punt'] for item in estaciones_con_reservas]
    estaciones_data = []
    
    for estacion_id in estaciones_ids:
        try:
            estacion = EstacioCarrega.objects.get(id_punt=estacion_id)
            reservas = Reserva.objects.filter(estacion=estacion).count()
            valoracion_media = ValoracionEstacion.objects.filter(estacion=estacion).aggregate(Avg('puntuacion'))['puntuacion__avg'] or 0
            
            estaciones_data.append({
                'estacion': estacion,
                'reservas': reservas,
                'valoracion_media': round(valoracion_media, 1)
            })
        except EstacioCarrega.DoesNotExist:
            continue
    
    # Estaciones mejor valoradas
    estaciones_valoradas = ValoracionEstacion.objects.values('estacion__id_punt').annotate(
        valoracion_media=Avg('puntuacion'),
        total_valoraciones=Count('id')
    ).filter(total_valoraciones__gte=3).order_by('-valoracion_media')[:10]
    
    estaciones_valoradas_ids = [item['estacion__id_punt'] for item in estaciones_valoradas]
    estaciones_valoradas_data = []
    
    for estacion_id in estaciones_valoradas_ids:
        try:
            estacion = EstacioCarrega.objects.get(id_punt=estacion_id)
            valoraciones = ValoracionEstacion.objects.filter(estacion=estacion)
            valoracion_media = valoraciones.aggregate(Avg('puntuacion'))['puntuacion__avg'] or 0
            total_valoraciones = valoraciones.count()
            
            estaciones_valoradas_data.append({
                'estacion': estacion,
                'valoracion_media': round(valoracion_media, 1),
                'total_valoraciones': total_valoraciones
            })
        except EstacioCarrega.DoesNotExist:
            continue
    
    context = {
        'estaciones_data': estaciones_data,
        'estaciones_valoradas_data': estaciones_valoradas_data,
    }
    
    return render(request, 'admin/estadisticas_estaciones.html', context)