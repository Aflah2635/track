from django.db import models
from django.core.cache import cache

class MaintenanceState(models.Model):
    is_maintenance = models.BooleanField(default=False)
    is_read_only = models.BooleanField(default=False)
    expected_duration = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. '2 hours', '15 mins'")
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    logging_channel_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "System Control"
        verbose_name_plural = "System Control"

    def save(self, *args, **kwargs):
        # Import inside to avoid circular dependency
        from apps.audit.utils import log_to_discord, LogEvents, LogColors
        
        # Check for changes if not new
        is_new = self.pk is None
        old_maintenance = None
        old_read_only = None
        
        if not is_new:
            try:
                old = MaintenanceState.objects.get(pk=self.pk)
                old_maintenance = old.is_maintenance
                old_read_only = old.is_read_only
            except MaintenanceState.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        cache.set('maintenance_mode', self.is_maintenance, timeout=None)
        cache.set('read_only_mode', self.is_read_only, timeout=None)
        
        # Log Maintenance Change
        if old_maintenance is not None and old_maintenance != self.is_maintenance:
            status = "ENABLED" if self.is_maintenance else "DISABLED"
            color = LogColors.WARNING if self.is_maintenance else LogColors.SUCCESS
            details = {'Status': status}
            if self.is_maintenance and self.expected_duration:
                details['Duration'] = self.expected_duration
                
            log_to_discord(
                event_type=LogEvents.MAINTENANCE,
                title=f"Maintenance {status}",
                user=self.updated_by or "System",
                details=details,
                color=color
            )
            
        # Log Read-Only Change
        if old_read_only is not None and old_read_only != self.is_read_only:
            status = "ENABLED" if self.is_read_only else "DISABLED"
            color = LogColors.WARNING if self.is_read_only else LogColors.SUCCESS
            log_to_discord(
                event_type=LogEvents.MAINTENANCE,
                title=f"Read-Only Mode {status}",
                user=self.updated_by or "System",
                details={'Status': status},
                color=color
            )

    @classmethod
    def is_active(cls):
        # Try to get from cache first
        is_maintenance = cache.get('maintenance_mode')
        if is_maintenance is None:
            obj, created = cls.objects.get_or_create(pk=1)
            is_maintenance = obj.is_maintenance
            cache.set('maintenance_mode', is_maintenance, timeout=None)
        return is_maintenance

    @classmethod
    def is_read_only_mode(cls):
        is_read_only = cache.get('read_only_mode')
        if is_read_only is None:
            obj, created = cls.objects.get_or_create(pk=1)
            is_read_only = obj.is_read_only
            cache.set('read_only_mode', is_read_only, timeout=None)
        return is_read_only

    @classmethod
    def set_state(cls, maintenance=None, read_only=None, user_id=None, duration=None):
        obj, created = cls.objects.get_or_create(pk=1)
        if maintenance is not None:
            obj.is_maintenance = maintenance
        if read_only is not None:
            obj.is_read_only = read_only
        
        # Only update duration if we are setting maintenance to True or explicitly passing duration
        if maintenance is True and duration:
            obj.expected_duration = duration
        elif maintenance is False:
            obj.expected_duration = None  # Clear duration when turning off
        
        if user_id:
            obj.updated_by = str(user_id)
        obj.save()
        return obj
