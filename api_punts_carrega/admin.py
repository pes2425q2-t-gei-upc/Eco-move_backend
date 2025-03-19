from django.contrib import admin
from .models import Ubicacio, EstacioCarrega, PuntCarrega, TipusCarregador, Reserva

# Register your models here.
admin.site.register(Ubicacio)
admin.site.register(EstacioCarrega)
admin.site.register(PuntCarrega)
admin.site.register(TipusCarregador)
admin.site.register(Reserva)
