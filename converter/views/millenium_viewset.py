from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.permissions import IsStaffOrAdmin
from converter.models.millenium_model import MilleniumFile
from converter.serializers.millenium_serializers import (
    MilleniumFileSerializer,
    MilleniumFileSerializerDetails,
)


class MilleniumUploadViewSet(ModelViewSet):
    queryset = MilleniumFile.objects.all().order_by("-created_at")
    permission_classes = [IsStaffOrAdmin]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return MilleniumFileSerializerDetails
        return MilleniumFileSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # overwrite: apenas 1 PDF ativo
        MilleniumFile.objects.all().delete()

        obj = MilleniumFile.objects.create(
            file=ser.validated_data["file"],
            uploaded_by=request.user,
        )

        out = MilleniumFileSerializerDetails(obj, context={"request": request}).data
        return Response(
            {"ok": True, "bank": "millenium", "data": out},
            status=status.HTTP_201_CREATED,
        )
