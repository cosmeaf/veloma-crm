# services/middleware/session_touch.py
import logging
from django.utils import timezone
from authentication.models import UserSession

logger = logging.getLogger(__name__)


class SessionTouchMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            try:
                # Atualiza apenas se existir sessão ativa (respeita sessão única)
                UserSession.objects.filter(user=user).update(last_seen=timezone.now())
            except Exception:
                logger.exception("Session touch failed | user=%s", user.email)

        return response