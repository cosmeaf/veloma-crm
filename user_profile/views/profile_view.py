import logging
from rest_framework.viewsets import ModelViewSet
from services.middleware.permissions import IsOwnerOrStaff
from user_profile.models import UserProfile
from user_profile.serializers import UserProfileSerializer, UserProfileDetailSerializer

logger = logging.getLogger(__name__)


class UserProfileViewSet(ModelViewSet):
    permission_classes = [IsOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserProfileDetailSerializer
        return UserProfileSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
