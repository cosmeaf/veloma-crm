from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from converter.models.file_model import ConverterFile
from converter.serializers.file_serializers import (
    ConverterFileSerializer,
    ConverterFileSerializerDetails,
)


class ConverterFileViewSet(ModelViewSet):
    queryset = ConverterFile.objects.all().order_by("-created_at")
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return ConverterFileSerializerDetails
        return ConverterFileSerializer

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(uploaded_by=self.request.user)
