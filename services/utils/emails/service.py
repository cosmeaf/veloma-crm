# services/utils/emails/service.py
import logging
from typing import Dict, Any, Sequence, Optional, Tuple

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailEnqueueError(RuntimeError):
    """Exceção levantada quando não consegue enfileirar o e-mail no Celery."""
    pass


class EmailService:
    """
    Serviço centralizado de envio de e-mails assíncronos via Celery.
    Garante:
    - Renderização segura de templates
    - Payload sempre válido (nunca falta 'text')
    - Logging completo em caso de erro (enfileiramento ou renderização)
    - Zero bloqueio na requisição do usuário
    """

    def __init__(
        self,
        *,
        subject: str,
        to: Sequence[str],
        template: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None,
        html: Optional[str] = None,
        cc: Optional[Sequence[str]] = None,
        bcc: Optional[Sequence[str]] = None,
        attachments: Optional[Sequence[Tuple[str, bytes, str]]] = None,
        from_email: Optional[str] = None,
        raise_on_failure: bool = False,
    ):
        self.subject = str(subject).strip()
        self.to = [email.strip() for email in to if email.strip()]
        self.template = template
        self.context = context or {}
        self.provided_text = text
        self.provided_html = html
        self.cc = [email.strip() for email in (cc or []) if email.strip()]
        self.bcc = [email.strip() for email in (bcc or []) if email.strip()]
        self.attachments = list(attachments or [])
        self.from_email = (from_email or settings.DEFAULT_FROM_EMAIL).strip()
        self.raise_on_failure = raise_on_failure

        if not self.to:
            raise ValueError("Pelo menos um destinatário válido é obrigatório.")

    def _render_templates(self) -> Tuple[str, str]:
        """Renderiza templates com fallback seguro e logging."""
        if self.provided_text is not None and self.provided_html is not None:
            return self.provided_text.strip(), self.provided_html.strip()

        if not self.template:
            raise ValueError("Você deve fornecer 'template' ou 'text' + 'html'.")

        try:
            html_content = render_to_string(f"{self.template}.html", self.context)
        except Exception as exc:
            logger.error(
                "Erro ao renderizar template HTML: %s.html | context=%s",
                self.template,
                list(self.context.keys()),
                exc_info=True,
            )
            raise EmailEnqueueError(f"Template HTML não encontrado: {self.template}.html") from exc

        try:
            text_content = render_to_string(f"{self.template}.txt", self.context)
        except Exception:
            logger.warning(
                "Template TXT não encontrado (%s.txt). Usando fallback de strip_tags.",
                self.template,
            )
            text_content = strip_tags(html_content)

        return text_content.strip(), html_content.strip()

    def get_payload(self) -> Dict[str, Any]:
        """Garante que o payload sempre tenha 'text' (nunca None ou ausente)."""
        text, html = self._render_templates()

        return {
            "subject": self.subject,
            "text": text or strip_tags(html or ""),  # fallback extremo: garante que 'text' exista
            "html": html,
            "from_email": self.from_email,
            "to": self.to,
            "cc": self.cc,
            "bcc": self.bcc,
            "attachments": self.attachments,
        }

    def send(self) -> Optional[str]:
        """
        Enfileira o e-mail no Celery com import lazy e logging completo.
        Retorna task_id em caso de sucesso.
        """
        try:
            from services.tasks.email_task import send_email_task  # Import local → sem circular import

            payload = self.get_payload()
            result = send_email_task.delay(payload)

            logger.info(
                "E-mail enfileirado com sucesso | task_id=%s | subject='%s' | to=%s | cc=%s | attachments=%d",
                result.id,
                self.subject,
                self.to,
                self.cc,
                len(self.attachments),
            )
            return result.id

        except Exception as exc:
            error_details = {
                "subject": self.subject,
                "to": self.to,
                "cc": self.cc,
                "template": self.template,
                "has_attachments": bool(self.attachments),
                "context_keys": list(self.context.keys()) if self.context else [],
            }

            logger.error(
                "FALHA CRÍTICA AO ENFILEIRAR E-MAIL | subject='%s' | to=%s | template='%s' | erro=%s",
                self.subject,
                self.to,
                self.template or "manual",
                str(exc),
                exc_info=True,
                extra=error_details,
            )

            if self.raise_on_failure or settings.DEBUG:
                raise EmailEnqueueError(f"Não foi possível enfileirar e-mail: {self.subject}") from exc

            return None