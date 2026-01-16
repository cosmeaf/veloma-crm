from django.db import models
from .base import AuditModel
from .profile import UserProfile


class BancoCredential(AuditModel):
    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="bank_credentials",
    )

    bank_name = models.CharField(max_length=120)
    iban = models.CharField(max_length=34, blank=True, default="")
    username = models.CharField(max_length=255)

    # segredo externo (NÃO é password do Django)
    secret_encrypted = models.TextField()

    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("profile", "bank_name", "username")

    def __str__(self):
        return f"{self.bank_name} | {self.profile.nif}"