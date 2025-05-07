from rest_framework.permissions import BasePermission, SAFE_METHODS

class EsElMismoUsuarioOReadOnly(BasePermission):
    """
    Permite GET a cualquiera, pero solo el propietario puede modificar.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user
