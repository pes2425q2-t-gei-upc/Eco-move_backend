from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
import requests
import json

from api_punts_carrega.models import (
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
    
    return render(request, 'admin_connect/dashboard.html', context)

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
        
        return redirect('admin_connect:sincronizar_refugios')
    
    refugios = RefugioClimatico.objects.all().order_by('nombre')
    
    context = {
        'refugios': refugios,
    }
    
    return render(request, 'admin_connect/sincronizar_refugios.html', context)

@staff_member_required
def gestionar_usuarios(request):
    usuarios = Usuario.objects.all().order_by('username')
    
    context = {
        'usuarios': usuarios,
    }
    
    return render(request, 'admin_connect/gestionar_usuarios.html', context)

@staff_member_required
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
     
    if request.method == 'POST':
        # Obtener datos del formulario
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        telefon = request.POST.get('telefon')
        idioma = request.POST.get('idioma')
        descripcio = request.POST.get('descripcio')
        is_admin = request.POST.get('is_admin') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        new_password = request.POST.get('new_password')
         
        # Verificar si el username ya existe (excluyendo el usuario actual)
        if Usuario.objects.filter(username=username).exclude(id=usuario_id).exists():
             messages.error(request, f'El nombre de usuario {username} ya está en uso.')
             return redirect('admin_connect/editar_usuario', usuario_id=usuario_id)
         
        # Verificar si el email ya existe (excluyendo el usuario actual)
        if Usuario.objects.filter(email=email).exclude(id=usuario_id).exists():
             messages.error(request, f'El email {email} ya está en uso.')
             return redirect('admin_connect/editar_usuario', usuario_id=usuario_id)
         
         # Actualizar datos del usuario
        usuario.username = username
        usuario.email = email
        usuario.first_name = first_name
        usuario.last_name = last_name
        usuario.telefon = telefon
        usuario.idioma = idioma
        usuario.descripcio = descripcio
        usuario.is_admin = is_admin
        usuario.is_staff = is_admin  # Actualizar is_staff junto con is_admin
        usuario.is_active = is_active
         
         # Actualizar contraseña si se proporciona una nueva
        if new_password:
            usuario.set_password(new_password)
         
        usuario.save()
        messages.success(request, f'Usuario {username} actualizado correctamente.')
        return redirect('admin_connect:gestionar_usuarios')
     
    context = {
         'usuario': usuario,
    }
     
    return render(request, 'admin_connect/editar_usuario.html', context)


@staff_member_required
def modificar_puntos_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        puntos = request.POST.get('puntos')
        #print(f"Acción: {accion}, Puntos: {puntos}")
        try:
            puntos = int(puntos)
            if accion == 'sumar':
                usuario.sumar_punts(puntos)
                messages.success(request, f'Se han sumado {puntos} puntos a {usuario.username}')
            elif accion == 'restar':
                usuario.restar_punts(puntos)
                messages.success(request, f'Se han restado {puntos} puntos a {usuario.username}')
            
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('admin_connect:gestionar_usuarios')
    
    context = {
        'usuario': usuario,
    }
    
    return render(request, 'admin_connect/modificar_puntos.html', context)

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
    ).order_by('-valoracion_media')[:10]
    
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
    
    return render(request, 'admin_connect/estadisticas_estaciones.html', context)