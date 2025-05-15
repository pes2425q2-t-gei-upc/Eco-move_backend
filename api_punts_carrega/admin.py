from django.contrib import admin
from django.utils.html import format_html
from api_punts_carrega.models import (
    Punt, EstacioCarrega, TipusCarregador, Reserva, Vehicle, 
    ModelCotxe, RefugioClimatico, Usuario, ValoracionEstacion,
    TextItem, ReporteEstacion,
)

class TipusCarregadorInline(admin.TabularInline):
    model = EstacioCarrega.tipus_carregador.through
    extra = 1
    verbose_name = "Tipo de cargador"
    verbose_name_plural = "Tipos de cargadores"

@admin.register(EstacioCarrega)
class EstacioCarregaAdmin(admin.ModelAdmin):
    list_display = ('id_punt', 'direccio', 'ciutat', 'potencia', 'get_tipus_velocitat', 'get_places')
    list_filter = ('ciutat', 'tipus_velocitat', 'potencia')
    search_fields = ('id_punt', 'direccio', 'ciutat')
    inlines = [TipusCarregadorInline]
    exclude = ('tipus_carregador',)
    
    def get_tipus_velocitat(self, obj):
        return ", ".join([t.nom_velocitat for t in obj.tipus_velocitat.all()])
    get_tipus_velocitat.short_description = "Velocidad de carga"
    
    def get_places(self, obj):
        return obj.nplaces or "No especificado"
    get_places.short_description = "Plazas"

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'estacion', 'fecha', 'hora', 'duracion', 'vehicle')
    list_filter = ('fecha', 'estacion')
    search_fields = ('estacion__id_punt', 'vehicle__matricula')
    date_hierarchy = 'fecha'

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'model_cotxe', 'propietari', 'carrega_actual', 'capacitat_bateria')
    list_filter = ('model_cotxe__marca',)
    search_fields = ('matricula', 'propietari__username', 'model_cotxe__marca', 'model_cotxe__model')

@admin.register(ModelCotxe)
class ModelCotxeAdmin(admin.ModelAdmin):
    list_display = ('marca', 'model', 'any_model')
    list_filter = ('marca', 'any_model')
    search_fields = ('marca', 'model')

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_admin', 'punts')
    list_filter = ('is_admin', 'idioma')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'idioma', 'telefon', 'descripcio', 'foto')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_admin', 'is_superuser', 'groups', 'user_permissions')}),
        ('Puntos', {'fields': ('_punts',)}),
    )

@admin.register(RefugioClimatico)
class RefugioClimaticoAdmin(admin.ModelAdmin):
    list_display = ('id_punt', 'nombre', 'direccio', 'lat', 'lng')
    search_fields = ('nombre', 'direccio')

@admin.register(ValoracionEstacion)
class ValoracionEstacionAdmin(admin.ModelAdmin):
    list_display = ('estacion', 'usuario', 'puntuacion', 'fecha_creacion')
    list_filter = ('puntuacion', 'fecha_creacion')
    search_fields = ('estacion__id_punt', 'usuario__username', 'comentario')

@admin.register(TipusCarregador)
class TipusCarregadorAdmin(admin.ModelAdmin):
    list_display = ('id_carregador', 'nom_tipus', 'tipus_connector', 'tipus_corrent')
    list_filter = ('tipus_corrent',)
    search_fields = ('nom_tipus', 'tipus_connector')

@admin.register(TextItem)
class TextItemAdmin(admin.ModelAdmin):
    list_display = ('key', 'text_ca', 'text_en', 'text_es')
    search_fields = ('key',)

@admin.register(ReporteEstacion)
class ReporteEstacionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'estacion',
        'tipo_error_display',
        'estado_display',
        'usuario_reporta',
        'fecha_reporte',
        'fecha_ultima_modificacion',
    )

    list_filter = (
        'estado',
        'tipo_error',
        'fecha_reporte',
        'estacion',
    )

    search_fields = (
        'id',
        'estacion__id_punt',
        'estacion__direccio',
        'usuario_reporta__username',
        'usuario_reporta__email',
        'comentario_usuario',
    )

    readonly_fields = (
        'fecha_reporte',
        'fecha_ultima_modificacion',
        'usuario_reporta',
    )

    fieldsets = (
        (None, {
            'fields': ('estacion', 'tipo_error', 'comentario_usuario')
        }),
        ('Gestión del Reporte', {
            'fields': ('estado', 'fecha_reporte', 'fecha_ultima_modificacion', 'usuario_reporta')
        }),
    )

    def tipo_error_display(self, obj):
        return obj.get_tipo_error_display()
    tipo_error_display.short_description = 'Tipo de Error'

    def estado_display(self, obj):
        return obj.get_estado_display()
    estado_display.short_description = 'Estado'

