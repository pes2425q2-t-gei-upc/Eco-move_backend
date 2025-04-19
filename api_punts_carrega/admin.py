from django.contrib import admin
from .models import  (
    EstacioCarrega,  
    TipusCarregador, 
    Reserva, 
    Usuario,
    Punt,
    ReservaFinalitzada,
    Vehicle,
    ModelCotxe,
    Report,
    RespostaReport,
    Descomptes,
    DataDescompte,  
)

# Register your models here.
admin.site.register(EstacioCarrega)
admin.site.register(TipusCarregador)
admin.site.register(Reserva)
admin.site.register(Usuario)
admin.site.register(Punt)
admin.site.register(ReservaFinalitzada)
admin.site.register(Vehicle)
admin.site.register(ModelCotxe)
admin.site.register(Report)
admin.site.register(RespostaReport)
admin.site.register(Descomptes)
admin.site.register(DataDescompte)