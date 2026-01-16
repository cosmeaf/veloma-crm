# services/tasks/login_alert_task.py
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from services.utils.emails.service import EmailService

logger = logging.getLogger(__name__)
User = get_user_model()


def _geo_lookup(ip: str) -> dict:
    if not getattr(settings, "LOGIN_ALERT_GEOLOOKUP_ENABLED", True):
        return {}

    try:
        import requests
        url = settings.LOGIN_ALERT_GEOLOOKUP_URL.format(ip=ip)
        timeout = getattr(settings, "LOGIN_ALERT_GEOLOOKUP_TIMEOUT", 3)
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        return {
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country_name") or data.get("country"),
        }
    except Exception as e:
        logger.warning("Geo lookup falhou para IP %s: %s", ip, e)
        return {}


@shared_task(bind=True, max_retries=3, default_retry_delay=120, retry_backoff=True)
def send_login_alert_task(self, user_id: int, ip: str, user_agent: str) -> None:
    try:
        user = User.objects.only("id", "email", "first_name").get(id=user_id)

        geo = _geo_lookup(ip)

        context = {
            "first_name": (user.first_name or "").strip() or "Usuário",
            "email": user.email,
            "ip": ip,
            "user_agent": user_agent,
            "city": geo.get("city", "Desconhecida"),
            "region": geo.get("region", ""),
            "country": geo.get("country", "Desconhecido"),
            "when": timezone.now().strftime("%d/%m/%Y às %H:%M"),
            "year": timezone.now().year,
        }

        # Usa SEMPRE o EmailService → garante payload correto com "text"
        task_id = EmailService(
            subject="Novo login detectado na sua conta",
            to=[user.email],
            template="emails/login_alert",
            context=context,
        ).send()

        if task_id:
            logger.info("Alerta de login enfileirado com sucesso | user=%s | ip=%s | task_id=%s", user.email, ip, task_id)
        else:
            logger.error("Falha ao enfileirar alerta de login | user=%s | ip=%s", user.email, ip)

    except User.DoesNotExist:
        logger.error("Usuário não encontrado para alerta de login | user_id=%s", user_id)
    except Exception as exc:
        logger.exception("Erro crítico na task send_login_alert_task | user_id=%s | ip=%s", user_id, ip)
        raise self.retry(exc=exc)