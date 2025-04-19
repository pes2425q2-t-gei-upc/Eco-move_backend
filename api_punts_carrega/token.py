from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    username_field = Usuario.EMAIL_FIELD  # usa el campo 'email' como identificador

    def validate(self, attrs):
        # Validar credenciales
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(request=self.context.get("request"), email=email, password=password)

            if not user:
                raise serializers.ValidationError("Correo o contraseña incorrectos", code="authorization")
        else:
            raise serializers.ValidationError("Debe proporcionar 'email' y 'password'", code="authorization")

        # Generar token
        data = super().validate(attrs)

        # Añadir info del usuario al response
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "punts": self.user.punts,
        }

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
