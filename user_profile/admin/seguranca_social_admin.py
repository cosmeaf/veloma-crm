from django.contrib import admin
from user_profile.models import SegurancaSocialDireta


@admin.register(SegurancaSocialDireta)
class SegurancaSocialAdmin(admin.ModelAdmin):
    list_display = ("profile", "niss", "last_verified_at")
    search_fields = ("profile__nif", "profile__legal_name", "niss")
    readonly_fields = ("password_encrypted", "created_at", "updated_at", "created_by", "updated_by")

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
