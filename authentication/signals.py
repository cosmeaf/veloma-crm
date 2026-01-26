from datetime import datetime
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.conf import settings
from services.utils.emails.service import EmailService
from services.utils.auth.login_notifier import notify_login

import logging
logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    logger.info(f"Login detectado via signal para {user.email} (ID: {user.id})")

    try:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'unknown'))
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')

        notify_login(user_id=user.id, ip=ip, user_agent=user_agent)

        if getattr(settings, 'NOTIFY_LOGIN_EMAIL', False):
            _send_email_safe(
                EmailService(
                    subject="Novo login detectado na sua conta",
                    to=[user.email],
                    template="emails/login_notification",
                    context={
                        "user": user,
                        "ip": ip,
                        "user_agent": user_agent,
                        "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "year": datetime.now().year,
                    },
                )
            )
            logger.info(f"Solicitação de email de login enviada para {user.email}")
        else:
            logger.warning("NOTIFY_LOGIN_EMAIL=False → email de novo login NÃO enviado")

    except Exception:
        logger.exception(f"Erro ao processar notificação de login para usuário {user.id}")