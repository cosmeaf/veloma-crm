from django.contrib import admin
from user_profile.models import FinancasPortal


@admin.register(FinancasPortal)
class FinancasPortalAdmin(admin.ModelAdmin):
    list_display = ("profile", "username", "two_factor_enabled", "last_verified_at")
    search_fields = ("profile__nif", "profile__legal_name", "username")
    readonly_fields = ("password_encrypted", "created_at", "updated_at", "created_by", "updated_by")

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)