from django.db import models
from .base import AuditModel
from .profile import UserProfile


class SegurancaSocialDireta(AuditModel):
    profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="seguranca_social_portal",
    )

    niss = models.CharField(max_length=20)
    password_encrypted = models.TextField()

    last_verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Segurança Social | {self.profile.nif}"
