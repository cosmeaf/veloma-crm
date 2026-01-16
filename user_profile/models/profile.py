from django.conf import settings
from django.db import models
from .base import AuditModel


class UserProfile(AuditModel):
    PERSON_TYPE_CHOICES = (
        ("PF", "Pessoa Física"),
        ("PJ", "Pessoa Jurídica"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="user_profile",
    )

    nif = models.CharField(max_length=20, unique=True)
    person_type = models.CharField(max_length=2, choices=PERSON_TYPE_CHOICES)

    legal_name = models.CharField(max_length=255)
    trade_name = models.CharField(max_length=255, blank=True, default="")

    phone = models.CharField(max_length=40, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nif} - {self.legal_name}"
