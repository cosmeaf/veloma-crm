# core/middleware.py
import logging
import traceback

logger = logging.getLogger("core.middleware")


class ApiExceptionLoggingMiddleware:
    """
    Middleware para:
    - Logar exceptions não tratadas
    - Nunca deixar erro silencioso
    - Garantir rastreabilidade
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response

        except Exception as exc:
            user = getattr(request, "user", None)

            logger.exception("Unhandled exception in API", extra={
                "path": getattr(request, "path", None),
                "method": getattr(request, "method", None),
                "user_id": getattr(user, "id", None) if user else None,
                "user_email": getattr(user, "email", None) if user else None,
                "exception": str(exc),
                "traceback": traceback.format_exc(),
            })

            # Re-raise para DRF/Django tratar (500 padrão)
            raise
