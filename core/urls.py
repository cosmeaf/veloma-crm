from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

def healthcheck(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    # Schema OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # Redoc
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include("api.urls.millennium_urls")),
    path("api/v1/auth/", include("authentication.urls")),
    path("api/v1/user-profile/", include("user_profile.urls")),

    path("", include("app.urls")),

    path("health/", healthcheck),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
