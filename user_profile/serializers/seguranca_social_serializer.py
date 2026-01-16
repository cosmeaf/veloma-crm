from rest_framework import serializers
from user_profile.models import SegurancaSocialDireta
from services.utils.crypto.fernet_cipher import FernetCipher


class SegurancaSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = SegurancaSocialDireta
        fields = [
            "id",
            "profile",
            "niss",
            "last_verified_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SegurancaSocialDetailSerializer(SegurancaSocialSerializer):
    password = serializers.SerializerMethodField()

    def get_password(self, obj) -> str:
        request = self.context.get("request")
        if request and (request.user.is_staff or request.user.is_superuser):
            return FernetCipher().decrypt(obj.password_encrypted)
        return "hidden"

    class Meta(SegurancaSocialSerializer.Meta):
        fields = SegurancaSocialSerializer.Meta.fields + ["password"]


class SegurancaSocialWriteSerializer(SegurancaSocialSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta(SegurancaSocialSerializer.Meta):
        fields = SegurancaSocialSerializer.Meta.fields + ["password"]

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