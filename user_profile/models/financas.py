from django.db import models
from .base import AuditModel
from .profile import UserProfile


class FinancasPortal(AuditModel):
    profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="financas_portal",
    )

    username = models.CharField(max_length=255)
    password_encrypted = models.TextField()

    recovery_email = models.EmailField(blank=True, default="")
    two_factor_enabled = models.BooleanField(default=False)

    last_verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Finanças | {self.profile.nif}"