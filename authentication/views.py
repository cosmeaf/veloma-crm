# authentication/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from authentication.serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserRecoverySerializer,
    OtpVerifySerializer,
    ResetPasswordSerializer,
)

User = get_user_model()


class UserRegisterViewSet(viewsets.ModelViewSet):
    serializer_class = UserRegisterSerializer
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    http_method_names = ["post"]


class UserLoginViewSet(viewsets.ViewSet):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class UserRecoveryViewSet(viewsets.ViewSet):
    serializer_class = UserRecoverySerializer
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"detail": "Código de recuperação enviado para o seu e-mail."},
            status=status.HTTP_200_OK,
        )


class OtpVerifyViewSet(viewsets.ViewSet):
    serializer_class = OtpVerifySerializer
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        return Response(
            {
                "detail": "Código verificado com sucesso. Use o token para redefinir a senha.",
                "reset_token": validated_data["reset_token"],
                "expires_in": validated_data.get("expires_in", 3600),
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordViewSet(viewsets.ViewSet):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Senha alterada com sucesso. Você já pode fazer login."},
            status=status.HTTP_200_OK,
        )


class UserBlockViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        username = request.data.get("username")
        if not username:
            return Response(
                {"detail": "O campo 'username' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(username=username)
            user.is_active = False
            user.save(update_fields=["is_active"])
            return Response(
                {"detail": f"Usuário '{username}' bloqueado com sucesso."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuário não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )