import hashlib
from rest_framework import serializers
from converter.models.bradesco_model import BradescoFile


class BradescoFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BradescoFile
        fields = ["file"]

    def validate_file(self, value):
        if not value.name.lower().endswith(".pdf"):
            raise serializers.ValidationError("Apenas PDF é permitido.")
        return value


class BradescoFileSerializerDetails(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()
    filesize = serializers.SerializerMethodField()
    sha256 = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = BradescoFile
        fields = [
            "id",
            "uuid",
            "filename",
            "file_url",
            "filesize",
            "sha256",
            "status",
            "owner_name",
            "uploaded_by",
            "created_at",
        ]

    def get_filename(self, obj):
        return obj.file.name.split("/")[-1] if obj.file else None

    def get_filesize(self, obj):
        return obj.file.size if obj.file else None

    def get_sha256(self, obj):
        if not obj.file:
            return None
        h = hashlib.sha256()
        obj.file.open("rb")
        try:
            for chunk in obj.file.chunks(1024 * 1024):
                h.update(chunk)
        finally:
            obj.file.close()
        return h.hexdigest()

    def get_status(self, obj):
        return "uploaded" if obj.file else "missing"

    def get_owner_name(self, obj):
        if not obj.uploaded_by:
            return None
        first = obj.uploaded_by.first_name or ""
        last = obj.uploaded_by.last_name or ""
        full = f"{first} {last}".strip()
        return full or obj.uploaded_by.username

    def get_file_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return None
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url
