from rest_framework import serializers
from converter.models.file_model import ConverterFile


class ConverterFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConverterFile
        fields = [
            "id",
            "uuid",
            "file",
            "overwritten",
            "created_at",
        ]
        read_only_fields = ["id", "uuid", "overwritten", "created_at"]


class ConverterFileSerializerDetails(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()
    filesize = serializers.SerializerMethodField()

    class Meta:
        model = ConverterFile
        fields = [
            "id",
            "uuid",
            "filename",
            "filesize",
            "uploaded_by",
            "overwritten",
            "created_at",
            "updated_at",
        ]

    def get_filename(self, obj):
        return obj.file.name.split("/")[-1] if obj.file else None

    def get_filesize(self, obj):
        return obj.file.size if obj.file else None
