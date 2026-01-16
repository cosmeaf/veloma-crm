from rest_framework import serializers
from user_profile.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "nif",
            "person_type",
            "legal_name",
            "trade_name",
            "phone",
            "address",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class UserProfileDetailSerializer(UserProfileSerializer):
    class Meta(UserProfileSerializer.Meta):
        fields = UserProfileSerializer.Meta.fields
