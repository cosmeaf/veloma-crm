import logging
from datetime import datetime
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Group
from django.conf import settings
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.validators import UniqueValidator
from authentication.models import OtpCode, ResetPasswordToken
from services.utils.emails.service import EmailService
from services.utils.auth.auth_guard import guard_login, log_attempt
from services.utils.auth.login_context import get_login_context
from services.utils.auth.session_control import enforce_single_session

logger = logging.getLogger(__name__)
User = get_user_model()


def _get_user_role(user: User) -> str:
    """Retorna o nome do primeiro grupo ou 'user' como fallback."""
    return user.groups.first().name if user.groups.exists() else "user"


def _send_email_safe(service: EmailService) -> None:
    """Envia email com tratamento padronizado de falha."""
    try:
        service.send()
    except Exception:
        logger.exception(f"Falha ao enfileirar email: {service.subject}")


class NormalizedEmailField(serializers.EmailField):
    """Campo que normaliza email automaticamente."""
    def to_internal_value(self, data):
        return (data or "").lower().strip()


class UserRegisterSerializer(serializers.ModelSerializer):
    email = NormalizedEmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Este e-mail já está cadastrado.",
                lookup='iexact'
            )
        ]
    )
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        email = validated_data.pop("email")
        password = validated_data.pop("password")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            **validated_data,
        )

        group, _ = Group.objects.get_or_create(name="user")
        user.groups.add(group)

        _send_email_safe(
            EmailService(
                subject="Bem-vindo à plataforma",
                to=[user.email],
                template="emails/welcome",
                context={
                    "user": user,
                    "year": datetime.now().year,
                },
            )
        )

        return user

    def to_representation(self, instance: User):
        refresh = RefreshToken.for_user(instance)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": instance.id,
                "email": instance.email,
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "role": _get_user_role(instance),
            },
        }


class UserLoginSerializer(serializers.Serializer):
    email = NormalizedEmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        request = self.context["request"]
        email = data["email"]
        password = data["password"]

        ctx = get_login_context(request)
        ip = ctx["ip"]
        user_agent = ctx["user_agent"]

        guard_login(email=email, ip=ip)

        user = authenticate(request=request, username=email, password=password)
        if not user:
            log_attempt(email=email, ip=ip, success=False)
            raise serializers.ValidationError("Credenciais inválidas.")

        log_attempt(email=email, ip=ip, success=True)

        try:
            enforce_single_session(user=user, ip=ip, user_agent=user_agent)
        except Exception:
            logger.exception("Falha ao aplicar controle de sessão única")

        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": _get_user_role(user),
            },
        }


class UserRecoverySerializer(serializers.Serializer):
    email = NormalizedEmailField()

    def validate_email(self, email: str) -> str:
        if not User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("E-mail não encontrado.")
        return email

    def validate(self, attrs):
        user = User.objects.get(email__iexact=attrs["email"])

        otp = OtpCode.objects.create(user=user, code=OtpCode.generate_code())

        _send_email_safe(
            EmailService(
                subject="Código de recuperação de senha",
                to=[user.email],
                template="emails/password_recovery",
                context={
                    "user": user,                    # ← padronizado
                    "otp_code": otp.code,
                    "year": datetime.now().year,
                },
            )
        )

        return attrs


class OtpVerifySerializer(serializers.Serializer):
    email = NormalizedEmailField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        user = User.objects.filter(email__iexact=attrs["email"]).first()
        if not user:
            raise serializers.ValidationError("Código inválido ou e-mail não encontrado.")

        otp = (
            OtpCode.objects.filter(user=user, code=attrs["code"], is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp:
            raise serializers.ValidationError("Código incorreto ou não encontrado.")
        if not otp.is_valid():
            raise serializers.ValidationError("Código expirado.")

        with transaction.atomic():
            otp.is_used = True
            otp.save(update_fields=["is_used"])

            reset_token = ResetPasswordToken.objects.create(user=user)

        return {
            "reset_token": str(reset_token.token),
            "expires_in": 3600,
        }


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})

        token_obj = ResetPasswordToken.objects.filter(token=data["token"]).first()
        if not token_obj:
            raise serializers.ValidationError("Token inválido.")
        if not token_obj.is_valid():
            raise serializers.ValidationError("Token expirado ou já utilizado.")

        data["token_obj"] = token_obj
        return data

    def save(self, **kwargs):
        token_obj = self.validated_data.pop("token_obj")
        user = token_obj.user

        user.set_password(self.validated_data["password"])
        user.save(update_fields=["password"])

        # Opcional: invalidar sessões
        # from django.contrib.sessions.models import Session
        # Session.objects.filter(session_key__in=user.session_set.values_list("session_key", flat=True)).delete()

        token_obj.delete()

        _send_email_safe(
            EmailService(
                subject="Sua senha foi alterada com sucesso",
                to=[user.email],
                template="emails/password_changed",
                context={
                    "user": user,                    # ← padronizado
                    "year": datetime.now().year,
                },
            )
        )

        return {"message": "Senha redefinida com sucesso!"}