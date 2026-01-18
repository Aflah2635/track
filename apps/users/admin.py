from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'is_active', 'is_frozen', 'is_staff')
    list_filter = ('is_staff', 'is_active', 'is_frozen')
    search_fields = ('username', 'email', 'phone')
    ordering = ('username',)
    actions = ['freeze_users', 'unfreeze_users', 'force_logout_users']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Account Control', {'fields': ('phone', 'is_frozen', 'force_logout_time')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone', 'is_frozen')}),
    )

    def freeze_users(self, request, queryset):
        rows_updated = queryset.update(is_frozen=True)
        self.message_user(request, f"{rows_updated} user(s) successfully frozen.")
    freeze_users.short_description = "Freeze selected users"

    def unfreeze_users(self, request, queryset):
        rows_updated = queryset.update(is_frozen=False)
        self.message_user(request, f"{rows_updated} user(s) successfully unfrozen.")
    unfreeze_users.short_description = "Unfreeze selected users"

    def force_logout_users(self, request, queryset):
        now = timezone.now()
        rows_updated = queryset.update(force_logout_time=now)
        self.message_user(request, f"{rows_updated} user(s) will be forced to logout on next request.")
    force_logout_users.short_description = "Force logout selected users"
