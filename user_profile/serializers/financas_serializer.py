from rest_framework import serializers
from user_profile.models import FinancasPortal
from services.utils.crypto.fernet_cipher import FernetCipher


class FinancasPortalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancasPortal
        fields = [
            "id",
            "profile",
            "username",
            "recovery_email",
            "two_factor_enabled",
            "last_verified_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FinancasPortalDetailSerializer(FinancasPortalSerializer):
    password = serializers.SerializerMethodField()

    def get_password(self, obj) -> str:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return ""

        if request.user.is_staff or request.user.is_superuser:
            return FernetCipher().decrypt(obj.password_encrypted)

        return "hidden"

    class Meta(FinancasPortalSerializer.Meta):
        fields = FinancasPortalSerializer.Meta.fields + ["password"]


class FinancasPortalWriteSerializer(FinancasPortalSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta(FinancasPortalSerializer.Meta):
        fields = FinancasPortalSerializer.Meta.fields + ["password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        if not password:
             raise serializers.ValidationError({"password": "Este campo é obrigatório."})
        
        validated_data["password_encrypted"] = FernetCipher().encrypt(password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password is not None:
            validated_data["password_encrypted"] = FernetCipher().encrypt(password)
        return super().update(instance, validated_data)