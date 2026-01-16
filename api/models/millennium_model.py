from django.db import models

class MillenniumUpload(models.Model):
    pdf = models.FileField(upload_to="uploads/millennium/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Upload Millennium {self.id}"
