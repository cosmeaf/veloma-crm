from rest_framework.viewsets import ModelViewSet
from services.middleware.permissions import IsOwnerOrStaff
from user_profile.models import EFatura
from user_profile.serializers import EFaturaSerializer, EFaturaDetailSerializer, EFaturaWriteSerializer


class EFaturaViewSet(ModelViewSet):
    permission_classes = [IsOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return EFatura.objects.select_related("profile", "profile__user")
        return EFatura.objects.select_related("profile", "profile__user").filter(profile__user=user)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return EFaturaWriteSerializer
        if self.action == "retrieve":
            return EFaturaDetailSerializer
        return EFaturaSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
