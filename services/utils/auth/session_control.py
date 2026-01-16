# services/utils/auth/session_control.py
import uuid
import logging
from django.utils import timezone
from authentication.models import UserSession

logger = logging.getLogger(__name__)


def new_session_id() -> str:
    return str(uuid.uuid4())


def enforce_single_session(*, user, ip: str = "", user_agent: str = "") -> str:
    """
    Garante sessão única: deleta qualquer sessão anterior e cria uma nova.
    Retorna o session_id criado.
    """
    new_sid = new_session_id()

    try:
        # Remove qualquer sessão anterior do usuário
        UserSession.objects.filter(user=user).delete()

        # Cria nova sessão
        UserSession.objects.create(
            user=user,
            session_id=new_sid,
            ip_address=ip or "",
            user_agent=user_agent or "",
            last_seen=timezone.now(),
        )

        logger.info("Sessão única criada | user=%s | ip=%s", user.email, ip)
        return new_sid

    except Exception:
        logger.exception("Falha ao criar sessão única | user_id=%s", user.id)
        # Mesmo com erro, retorna um ID (não bloqueia login)
        return new_sid