import logging
from celery import shared_task
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, payload: dict) -> None:
    try:
        subject = (payload.get("subject") or "").strip()
        text = payload.get("text") or ""
        html = payload.get("html")
        from_email = payload.get("from_email")
        to = payload.get("to") or []
        cc = payload.get("cc") or []
        bcc = payload.get("bcc") or []
        attachments = payload.get("attachments") or []

        if not subject or not to:
            logger.error(
                "Payload inválido | subject=%s | to=%s | keys=%s",
                subject,
                to,
                list(payload.keys()),
            )
            return

        if not text and not html:
            logger.error(
                "E-mail sem conteúdo | subject=%s | to=%s",
                subject,
                to,
            )
            return

        email = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=from_email,
            to=to,
            cc=cc,
            bcc=bcc,
        )

        if html:
            email.attach_alternative(html, "text/html")

        for attachment in attachments:
            try:
                email.attach(*attachment)
            except Exception:
                logger.warning(
                    "Falha ao anexar | subject=%s | attachment=%s",
                    subject,
                    attachment,
                    exc_info=True,
                )

        email.send(fail_silently=False)

        logger.info("E-mail enviado | subject=%s | to=%s", subject, to)

    except Exception as exc:
        logger.exception(
            "Erro crítico no envio de e-mail | payload_keys=%s",
            list(payload.keys()),
        )
        raise self.retry(exc=exc)
