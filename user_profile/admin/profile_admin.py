from django.contrib import admin
from user_profile.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("nif", "legal_name", "person_type", "is_active", "user")
    list_filter = ("person_type", "is_active")
    search_fields = ("nif", "legal_name", "trade_name", "user__email")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
