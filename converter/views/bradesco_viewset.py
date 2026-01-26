from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.permissions import IsStaffOrAdmin
from converter.models.bradesco_model import BradescoFile
from converter.serializers.bradesco_serializers import (
    BradescoFileSerializer,
    BradescoFileSerializerDetails,
)


class BradescoUploadViewSet(ModelViewSet):
    queryset = BradescoFile.objects.all().order_by("-created_at")
    permission_classes = [IsStaffOrAdmin]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return BradescoFileSerializerDetails
        return BradescoFileSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        BradescoFile.objects.all().delete()

        obj = BradescoFile.objects.create(
            file=ser.validated_data["file"],
            uploaded_by=request.user,
        )

        out = BradescoFileSerializerDetails(obj, context={"request": request}).data
        return Response(
            {"ok": True, "bank": "bradesco", "data": out},
            status=status.HTTP_201_CREATED,
        )
