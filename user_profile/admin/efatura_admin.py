from django.contrib import admin
from user_profile.models import EFatura


@admin.register(EFatura)
class EFaturaAdmin(admin.ModelAdmin):
    list_display = ("profile", "access_mode", "custom_username", "last_verified_at")
    search_fields = ("profile__nif", "profile__legal_name", "custom_username")
    readonly_fields = ("custom_password_encrypted", "created_at", "updated_at", "created_by", "updated_by")

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)