import uuid
import random
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class LoginAttempt(models.Model):
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["email", "ip_address", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} | {self.ip_address} | {'OK' if self.success else 'FAIL'}"


class OtpCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @staticmethod
    def generate_code() -> str:
        return f"{random.randint(0, 999999):06d}"

    def is_valid(self) -> bool:
        return (timezone.now() - self.created_at) <= timedelta(minutes=10)


class ResetPasswordToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self) -> bool:
        return (timezone.now() - self.created_at) <= timedelta(minutes=30)


class UserSession(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="active_session",
    )
    session_id = models.CharField(max_length=64, unique=True)
    ip_address = models.CharField(max_length=64, blank=True, default="")
    user_agent = models.TextField(blank=True, default="")
    last_seen = models.DateTimeField(default=timezone.now)

    def touch(self):
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen"])

    def __str__(self):
        return f"{self.user.email} | {self.ip_address}"
