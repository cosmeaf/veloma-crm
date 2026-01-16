from datetime import timedelta
from django.utils import timezone
from authentication.models import LoginAttempt
from services.utils.auth.constants import LOGIN_MAX_ATTEMPTS, LOGIN_WINDOW_MINUTES


def failed_attempts(email: str, ip: str) -> int:
    since = timezone.now() - timedelta(minutes=LOGIN_WINDOW_MINUTES)
    return LoginAttempt.objects.filter(
        email=email,
        ip_address=ip,
        success=False,
        created_at__gte=since,
    ).count()


def is_blocked(email: str, ip: str) -> bool:
    return failed_attempts(email, ip) >= LOGIN_MAX_ATTEMPTS


def register_attempt(email: str, ip: str, success: bool) -> None:
    LoginAttempt.objects.create(
        email=email,
        ip_address=ip,
        success=success,
    )
