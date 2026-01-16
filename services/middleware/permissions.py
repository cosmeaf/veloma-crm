from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Permite acesso apenas ao dono do recurso.
    Espera que o model tenha o atributo `user`.
    """

    message = "Você não é o dono deste recurso."

    def has_object_permission(self, request, view, obj):
        return hasattr(obj, "user") and obj.user == request.user


class IsOwnerOrStaff(BasePermission):
    """
    Permite:
    - Dono do recurso
    - Staff
    - Superuser
    """

    message = "Acesso permitido apenas ao dono ou staff autorizado."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        return hasattr(obj, "user") and obj.user == request.user


class IsStaff(BasePermission):
    """
    Apenas staff ou admin.
    """

    message = "Acesso restrito à equipa da Veloma."

    def has_permission(self, request, view):
        return request.user.is_staff or request.user.is_superuser
