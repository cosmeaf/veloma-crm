from rest_framework import serializers
from user_profile.models import BancoCredential
from services.utils.crypto.fernet_cipher import FernetCipher


class BancoCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = BancoCredential
        fields = [
            "id",
            "profile",
            "bank_name",
            "iban",
            "username",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BancoCredentialDetailSerializer(BancoCredentialSerializer):
    password = serializers.SerializerMethodField()

    def get_password(self, obj) -> str:
        request = self.context.get("request")
        if request and (request.user.is_staff or request.user.is_superuser):
            return FernetCipher().decrypt(obj.secret_encrypted)
        return "hidden"

    class Meta(BancoCredentialSerializer.Meta):
        fields = BancoCredentialSerializer.Meta.fields + ["password"]


class BancoCredentialWriteSerializer(BancoCredentialSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta(BancoCredentialSerializer.Meta):
        fields = BancoCredentialSerializer.Meta.fields + ["password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        if not password:
            raise serializers.ValidationError({"password": "Este campo é obrigatório."})
        validated_data["secret_encrypted"] = FernetCipher().encrypt(password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password is not None:
            validated_data["secret_encrypted"] = FernetCipher().encrypt(password)
        return super().update(instance, validated_data)