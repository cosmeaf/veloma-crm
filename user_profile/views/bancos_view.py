from rest_framework.viewsets import ModelViewSet
from services.middleware.permissions import IsOwnerOrStaff
from user_profile.models import BancoCredential

# CORREÇÃO: O arquivo se chama 'bancos_serializer.py'
from user_profile.serializers.bancos_serializer import (
    BancoCredentialSerializer,
    BancoCredentialDetailSerializer,
    BancoCredentialWriteSerializer,
)


class BancoCredentialViewSet(ModelViewSet):
    permission_classes = [IsOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return BancoCredential.objects.select_related("profile", "profile__user")
        return BancoCredential.objects.filter(profile__user=user)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return BancoCredentialWriteSerializer
        if self.action == "retrieve":
            return BancoCredentialDetailSerializer
        return BancoCredentialSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)