from rest_framework import serializers
from user_profile.models import EFatura
from services.utils.crypto.fernet_cipher import FernetCipher


class EFaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EFatura
        fields = [
            "id",
            "profile",
            "access_mode",
            "custom_username",
            "last_verified_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EFaturaDetailSerializer(EFaturaSerializer):
    custom_password = serializers.SerializerMethodField()

    def get_custom_password(self, obj) -> str:
        request = self.context.get("request")
        if request and (request.user.is_staff or request.user.is_superuser):
            return FernetCipher().decrypt(obj.custom_password_encrypted)
        return "hidden"

    class Meta(EFaturaSerializer.Meta):
        fields = EFaturaSerializer.Meta.fields + ["custom_password"]


class EFaturaWriteSerializer(EFaturaSerializer):
    custom_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta(EFaturaSerializer.Meta):
        fields = EFaturaSerializer.Meta.fields + ["custom_password"]

    def create(self, validated_data):
        custom_password = validated_data.pop("custom_password", "")
        if custom_password:
            validated_data["custom_password_encrypted"] = FernetCipher().encrypt(custom_password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        custom_password = validated_data.pop("custom_password", None)
        if custom_password is not None:
            if custom_password == "":
                validated_data["custom_password_encrypted"] = ""
            else:
                validated_data["custom_password_encrypted"] = FernetCipher().encrypt(custom_password)
        return super().update(instance, validated_data)