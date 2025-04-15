from django.contrib import admin
from .models import  PuntEmergencia, Missatge, Chat

# Register your models here.
admin.site.register(PuntEmergencia)
admin.site.register(Missatge)
admin.site.register(Chat)
