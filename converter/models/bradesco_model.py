import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


def bradesco_upload_path(instance, filename):
    return f"converter/bradesco/upload/bradesco.{instance.uuid}.pdf"


class BradescoFile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    file = models.FileField(upload_to=bradesco_upload_path)

    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bradesco PDF"
        verbose_name_plural = "Bradesco PDFs"
