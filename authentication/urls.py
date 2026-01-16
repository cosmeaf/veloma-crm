from rest_framework.routers import DefaultRouter
from .views import (
    UserRegisterViewSet,
    UserLoginViewSet,
    UserRecoveryViewSet,
    OtpVerifyViewSet,
    ResetPasswordViewSet,
    UserBlockViewSet,
)

router = DefaultRouter()
router.register("register", UserRegisterViewSet, basename="register")
router.register("login", UserLoginViewSet, basename="login")
router.register("recovery", UserRecoveryViewSet, basename="recovery")
router.register("otp-verify", OtpVerifyViewSet, basename="otp-verify")
router.register("reset-password", ResetPasswordViewSet, basename="reset-password")
router.register("block-user", UserBlockViewSet, basename="block-user")

urlpatterns = router.urls
