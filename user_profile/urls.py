from rest_framework.routers import DefaultRouter
from user_profile.views import (
    UserProfileViewSet,
    FinancasPortalViewSet,
    SegurancaSocialViewSet,
    EFaturaViewSet,
    BancoCredentialViewSet,
)

router = DefaultRouter()
router.register("profiles", UserProfileViewSet, basename="user-profile")
router.register("financas", FinancasPortalViewSet, basename="financas")
router.register("seguranca-social", SegurancaSocialViewSet, basename="seguranca-social")
router.register("efatura", EFaturaViewSet, basename="efatura")
router.register("bancos", BancoCredentialViewSet, basename="bancos")

urlpatterns = router.urls
