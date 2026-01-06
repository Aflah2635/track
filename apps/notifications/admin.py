from django.contrib import admin
from .models import Notification, Broadcast

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'type', 'message', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'message')
    readonly_fields = ('created_at',)

@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ('message', 'type', 'created_at', 'sent')
    readonly_fields = ('sent', 'created_at')
    
    def save_model(self, request, obj, form, change):
        # The signal handles the actual sending
        super().save_model(request, obj, form, change)
