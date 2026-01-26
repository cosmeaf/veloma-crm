# core/permissions.py
import logging
from rest_framework.permissions import BasePermission

logger = logging.getLogger("core.permissions")


class IsStaffOrAdmin(BasePermission):
    """
    Permite acesso apenas para:
    - is_staff
    - is_superuser

    Robusto:
    - Nunca levanta exception
    - Loga inconsistências
    - Fallback seguro (nega acesso)
    """

    message = "Acesso permitido apenas para staff ou admin."

    def has_permission(self, request, view):
        try:
            user = getattr(request, "user", None)

            if not user:
                logger.warning("Permission check sem request.user", extra={
                    "path": getattr(request, "path", None),
                })
                return False

            if not user.is_authenticated:
                return False

            allowed = bool(user.is_staff or user.is_superuser)

            if not allowed:
                logger.info("Acesso negado (não staff/admin)", extra={
                    "user_id": getattr(user, "id", None),
                    "email": getattr(user, "email", None),
                    "path": getattr(request, "path", None),
                    "method": getattr(request, "method", None),
                })

            return allowed

        except Exception as exc:
            # NUNCA quebra a API por erro de permissão
            logger.exception("Erro inesperado em IsStaffOrAdmin", extra={
                "error": str(exc),
                "path": getattr(request, "path", None),
            })
            return False
