from django.db import models
from api_punts_carrega.models import Usuario


class Missatge(models.Model):
    id_missatge = models.AutoField(primary_key=True)
    chat = models.ForeignKey('Chat', on_delete=models.CASCADE, related_name="missatges")
    sender = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="missatges_enviats")
    content = models.TextField()
    timestamp = models.DateField(auto_now=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.remitent} dice: {self.text[:30]}"
    
class PuntEmergencia(models.Model):
    id_emergencia = models.AutoField(primary_key=True)
    sender = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="emergencies_sent")
    titol = models.CharField(max_length=100)
    descripcio = models.TextField()
    lat = models.FloatField(null=False)
    lng = models.FloatField(null=False)
    is_active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Emergència: {self.titol}"

class Chat(models.Model):
    alerta = models.ForeignKey(PuntEmergencia, on_delete=models.CASCADE, related_name="chats")
    creador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="chats_enviados")
    receptor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="chats_recibidos")
    activa = models.BooleanField(default=True)
    inicida_en = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Chat entre {self.creador} i {self.receptor} sobre {self.alerta.titol}"
