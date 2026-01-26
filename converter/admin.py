from django.contrib import admin
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from converter.models.file_model import ConverterFile


@admin.register(ConverterFile)
class ConverterFileAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "uploaded_by",
        "overwritten",
        "created_at",
        "updated_at",
    )

    readonly_fields = ("uuid", "created_at", "updated_at", "overwritten")

    def get_exclude(self, request, obj=None):
        """
        No CREATE: esconde uploaded_by
        No EDIT:
          - Superuser: pode alterar
          - Staff: não pode alterar
        """
        if obj is None:
            return ("uploaded_by",)

        if not request.user.is_superuser:
            return ("uploaded_by",)

        return ()

    def save_model(self, request, obj, form, change):
        """
        - No CREATE: seta owner automaticamente
        - No EDIT: audita troca de owner (apenas superuser)
        """
        old_owner = None
        if change:
            old_owner = (
                ConverterFile.objects
                .filter(pk=obj.pk)
                .values_list("uploaded_by", flat=True)
                .first()
            )

        if not change and not obj.uploaded_by:
            obj.uploaded_by = request.user

        super().save_model(request, obj, form, change)

        # Auditoria de troca de owner
        if change and request.user.is_superuser:
            new_owner = obj.uploaded_by_id

            if old_owner and old_owner != new_owner:
                LogEntry.objects.log_action(
                    user_id=request.user.id,
                    content_type_id=ContentType.objects.get_for_model(obj).pk,
                    object_id=obj.pk,
                    object_repr=str(obj),
                    action_flag=CHANGE,
                    change_message=(
                        f"Owner alterado de user_id={old_owner} "
                        f"para user_id={new_owner}"
                    ),
                )
