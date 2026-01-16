import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class CryptoConfigError(RuntimeError):
    pass


class FernetCipher:
    """
    Thin wrapper over Fernet encryption.
    Requires USER_PROFILE_ENCRYPTION_KEY in settings.
    """

    def __init__(self):
        try:
            from cryptography.fernet import Fernet
        except Exception as exc:
            raise CryptoConfigError("cryptography is required: pip install cryptography") from exc

        key = getattr(settings, "USER_PROFILE_ENCRYPTION_KEY", None)
        if not key:
            raise CryptoConfigError("Missing USER_PROFILE_ENCRYPTION_KEY in settings/.env")

        if isinstance(key, str):
            key = key.encode()

        self._fernet = Fernet(key)

    def encrypt(self, value: str) -> str:
        if value is None:
            return ""
        raw = value.encode("utf-8")
        return self._fernet.encrypt(raw).decode("utf-8")

    def decrypt(self, value: str) -> str:
        if not value:
            return ""
        raw = value.encode("utf-8")
        return self._fernet.decrypt(raw).decode("utf-8")
