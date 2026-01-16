from django.db import models
from .base import AuditModel
from .profile import UserProfile


class EFatura(AuditModel):
    profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="efatura",
    )

    access_mode = models.CharField(
        max_length=50,
        default="same_as_financas",
        help_text="same_as_financas or custom",
    )

    custom_username = models.CharField(max_length=255, blank=True, default="")
    custom_password_encrypted = models.TextField(blank=True, default="")

    last_verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return f"e-Fatura | {self.profile.nif}"