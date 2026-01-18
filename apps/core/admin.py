from django.contrib import admin
from .models import MaintenanceState

@admin.register(MaintenanceState)
class MaintenanceStateAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_maintenance', 'is_read_only', 'updated_at', 'updated_by')
    list_display_links = ('id',)
    list_editable = ('is_maintenance', 'is_read_only')
    readonly_fields = ('updated_at', 'updated_by')

    def has_add_permission(self, request):
        # Only allow one instance
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user.username
        super().save_model(request, obj, form, change)
