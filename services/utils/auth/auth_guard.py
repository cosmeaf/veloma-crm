import logging
from rest_framework.exceptions import ValidationError
from services.utils.auth.bruteforce import is_blocked, register_attempt

logger = logging.getLogger(__name__)


def guard_login(email: str, ip: str) -> None:
    if is_blocked(email, ip):
        logger.warning("Login bloqueado | email=%s | ip=%s", email, ip)
        raise ValidationError(
            "Muitas tentativas de login. Tente novamente mais tarde."
        )


def log_attempt(email: str, ip: str, success: bool) -> None:
    try:
        register_attempt(email=email, ip=ip, success=success)
    except Exception:
        logger.exception("Falha ao registrar tentativa de login")
