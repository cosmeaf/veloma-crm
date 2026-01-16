from rest_framework import serializers

class MillenniumUploadSerializer(serializers.Serializer):
    pdf = serializers.FileField()

    def validate_pdf(self, file):
        if not file.name.lower().endswith(".pdf"):
            raise serializers.ValidationError("Envie um arquivo PDF válido (.pdf).")

        if file.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Tamanho máximo permitido: 10MB.")

        return file
