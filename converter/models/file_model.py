import os
import uuid
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


def converter_upload_path(instance, filename):
    # Sempre usar o mesmo UUID lógico por registro
    return f"converter/upload/{instance.uuid}/{filename}"


class ConverterFile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    file = models.FileField(upload_to=converter_upload_path)
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="converter_uploads"
    )

    overwritten = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Upload de Excel"
        verbose_name_plural = "Uploads de Excel"

        
    def save(self, *args, **kwargs):
        # Detecta sobrescrita
        if self.pk:
            old = ConverterFile.objects.filter(pk=self.pk).first()
            if old and old.file and old.file != self.file:
                self.overwritten = True
                # Remove ficheiro antigo do disco
                if os.path.isfile(old.file.path):
                    try:
                        os.remove(old.file.path)
                    except Exception:
                        pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"ConverterFile {self.uuid}"
