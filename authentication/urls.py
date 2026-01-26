from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserRegisterViewSet,
    UserLoginViewSet,
    UserRecoveryViewSet,
    OtpVerifyViewSet,
    ResetPasswordViewSet,
    UserBlockViewSet,
)

router = DefaultRouter()
router.register(r"register", UserRegisterViewSet, basename="auth-register")
router.register(r"login", UserLoginViewSet, basename="auth-login")
router.register(r"recovery", UserRecoveryViewSet, basename="auth-recovery")
router.register(r"otp-verify", OtpVerifyViewSet, basename="auth-otp-verify")
router.register(r"reset-password", ResetPasswordViewSet, basename="auth-reset-password")
router.register(r"block-user", UserBlockViewSet, basename="auth-block-user")

urlpatterns = [
    # JWT refresh token
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

urlpatterns += router.urls
