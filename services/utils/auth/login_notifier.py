# services/utils/auth/login_notifier.py
import logging
from django.conf import settings
from services.tasks.login_alert_task import send_login_alert_task

logger = logging.getLogger(__name__)


def notify_login(*, user_id: int, ip: str, user_agent: str) -> None:
    if not getattr(settings, "LOGIN_ALERT_ENABLED", True):
        return

    try:
        send_login_alert_task.delay(user_id=user_id, ip=ip, user_agent=user_agent)
    except Exception:
        logger.exception("Failed to enqueue login alert | user_id=%s", user_id)