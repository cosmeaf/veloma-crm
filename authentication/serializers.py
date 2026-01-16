import logging
from datetime import datetime
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Group
from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import OtpCode, ResetPasswordToken
from services.utils.emails.service import EmailService
from services.utils.auth.auth_guard import guard_login, log_attempt
from services.utils.auth.login_context import get_login_context
from services.utils.auth.session_control import enforce_single_session
from services.utils.auth.login_notifier import notify_login


logger = logging.getLogger(__name__)
User = get_user_model()


def _get_user_role(user: User) -> str:
    """Helper para obter o role do usuário de forma consistente."""
    return user.groups.first().name if user.groups.exists() else "user"


def _send_email_safe(service: EmailService) -> None:
    """Envia email com tratamento de exceção padronizado."""
    try:
        service.send()
    except Exception:
        logger.exception(f"{service.subject} - email enqueue failed")


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email", "password", "password2")

    def validate_email(self, value: str) -> str:
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("E-mail já cadastrado.")
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError("As senhas não coincidem.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        email = validated_data.pop("email").lower().strip()
        password = validated_data.pop("password")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            **validated_data,
        )

        # Garante que o grupo 'user' exista e associe
        group, _ = Group.objects.get_or_create(name="user")
        user.groups.add(group)

        # Email de boas-vindas
        _send_email_safe(
            EmailService(
                subject="Bem-vindo à plataforma",
                to=[user.email],
                template="emails/welcome",
                context={
                    "first_name": (user.first_name or "").strip(),
                    "last_name": (user.last_name or "").strip(),
                    "email": user.email,
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
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        request = self.context["request"]
        email = data["email"].lower().strip()
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
            logger.exception("Falha no controle de sessão única")

        try:
            notify_login(user_id=user.id, ip=ip, user_agent=user_agent)
        except Exception:
            logger.exception("Falha ao notificar login")

        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.groups.first().name if user.groups.exists() else "user",
            },
        }



class UserRecoverySerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        email = value.lower().strip()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise serializers.ValidationError("E-mail não encontrado.")

        otp = OtpCode.objects.create(user=user, code=OtpCode.generate_code())

        _send_email_safe(
            EmailService(
                subject="Código de recuperação de senha",
                to=[user.email],
                template="emails/password_recovery",
                context={
                    "first_name": (user.first_name or "").strip(),
                    "otp_code": otp.code,
                    "year": datetime.now().year,
                },
            )
        )

        return email


class OtpVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data):
        email = data["email"].lower().strip()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise serializers.ValidationError("Código inválido.")

        otp = (
            OtpCode.objects.filter(user=user, code=data["code"], is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp or not otp.is_valid():
            raise serializers.ValidationError("Código inválido ou expirado.")

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        token = ResetPasswordToken.objects.create(user=user)
        reset_url = (
            f"{settings.FRONTEND_BASE_URL}{settings.AUTH_RESET_PASSWORD_PATH}"
            f"?token={token.token}"
        )

        return {"reset_url": reset_url}


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("As senhas não coincidem.")

        token_obj = ResetPasswordToken.objects.filter(token=data["token"]).first()
        if not token_obj or not token_obj.is_valid():
            raise serializers.ValidationError("Token inválido ou expirado.")

        data["token_obj"] = token_obj
        return data

    def save(self, **kwargs):
        token_obj = self.validated_data.pop("token_obj")
        user = token_obj.user

        user.set_password(self.validated_data["password"])
        user.save(update_fields=["password"])

        token_obj.delete()

        _send_email_safe(
            EmailService(
                subject="Senha alterada com sucesso",
                to=[user.email],
                template="emails/password_changed",
                context={
                    "first_name": (user.first_name or "").strip(),
                    "email": user.email,
                    "year": datetime.now().year,
                },
            )
        )

        return {"message": "Senha redefinida com sucesso!"}