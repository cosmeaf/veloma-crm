# services/utils/auth/login_context.py
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str:
    """
    Extrai o IP real do cliente de forma segura.
    Prioriza X-Forwarded-For, mas só o primeiro IP (evita spoofing).
    """
    if not request:
        return "0.0.0.0"

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Pega apenas o primeiro IP (o original do cliente)
        ip = x_forwarded_for.split(",")[0].strip()
        return ip

    # Headers comuns em proxies (NGINX, Cloudflare, etc.)
    for header in ("HTTP_X_REAL_IP", "HTTP_CF_CONNECTING_IP", "HTTP_X_CLIENT_IP"):
        ip = request.META.get(header)
        if ip:
            return ip.strip()

    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def get_user_agent(request) -> str:
    if not request:
        return "unknown"
    return request.META.get("HTTP_USER_AGENT", "unknown")


def get_login_context(request) -> dict:
    return {
        "ip": get_client_ip(request),
        "user_agent": get_user_agent(request),
    }