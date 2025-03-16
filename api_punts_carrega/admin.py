from django.contrib import admin
<<<<<<< Updated upstream

# Register your models here.
# admin.site.register(ChargingStation)
=======
from api_punts_carrega.models import Ubicacio, EstacioCarrega, PuntCarrega, TipusCarregador

# Register your models here.
admin.site.register(Ubicacio)
admin.site.register(EstacioCarrega)
admin.site.register(PuntCarrega)
admin.site.register(TipusCarregador)
>>>>>>> Stashed changes
