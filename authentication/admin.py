from django.contrib import admin, messages
from django.utils import timezone
from datetime import timedelta

from .models import (
    UserSession,
    OtpCode,
    ResetPasswordToken,
    LoginAttempt,
)

# =========================
# User Session Admin
# =========================
@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "ip_address",
        "user_agent_short",
        "last_seen",
        "is_online",
    )
    search_fields = ("user__email", "ip_address")
    readonly_fields = (
        "user",
        "session_id",
        "ip_address",
        "user_agent",
        "last_seen",
    )

    def user_agent_short(self, obj):
        return (obj.user_agent[:60] + "...") if obj.user_agent else "-"
    user_agent_short.short_description = "User Agent"

    def is_online(self, obj):
        return (timezone.now() - obj.last_seen).seconds < 300
    is_online.boolean = True
    is_online.short_description = "Online"


# =========================
# Login Attempt Admin
# =========================
@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "ip_address",
        "success_icon",
        "created_at",
        "is_blocked",
    )
    list_filter = ("success", "created_at")
    search_fields = ("email", "ip_address")
    date_hierarchy = "created_at"
    actions = ("unlock_email", "unlock_ip")

    def success_icon(self, obj):
        return obj.success
    success_icon.boolean = True
    success_icon.short_description = "Sucesso"

    def is_blocked(self, obj):
        window = timezone.now() - timedelta(minutes=15)
        failures = LoginAttempt.objects.filter(
            email=obj.email,
            ip_address=obj.ip_address,
            success=False,
            created_at__gte=window,
        ).count()
        return failures >= 5
    is_blocked.boolean = True
    is_blocked.short_description = "Bloqueado?"

    # =========================
    # ADMIN ACTIONS
    # =========================
    def unlock_email(self, request, queryset):
        emails = set(queryset.values_list("email", flat=True))
        deleted = LoginAttempt.objects.filter(
            email__in=emails,
            success=False,
        ).delete()[0]

        self.message_user(
            request,
            f"{deleted} tentativas removidas para os emails selecionados.",
            level=messages.SUCCESS,
        )
    unlock_email.short_description = "Desbloquear por EMAIL"

    def unlock_ip(self, request, queryset):
        ips = set(queryset.values_list("ip_address", flat=True))
        deleted = LoginAttempt.objects.filter(
            ip_address__in=ips,
            success=False,
        ).delete()[0]

        self.message_user(
            request,
            f"{deleted} tentativas removidas para os IPs selecionados.",
            level=messages.SUCCESS,
        )
    unlock_ip.short_description = "Desbloquear por IP"


# =========================
# OTP Admin
# =========================
@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "is_used", "created_at")
    list_filter = ("is_used", "created_at")
    search_fields = ("user__email",)


# =========================
# Reset Token Admin
# =========================
@admin.register(ResetPasswordToken)
class ResetPasswordTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at", "is_valid_token")
    search_fields = ("user__email",)

    def is_valid_token(self, obj):
        return obj.is_valid()
    is_valid_token.boolean = True
    is_valid_token.short_description = "Válido?"
