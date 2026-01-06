from django.db import models
from django.core.cache import cache

class MaintenanceState(models.Model):
    is_maintenance = models.BooleanField(default=False)
    is_read_only = models.BooleanField(default=False)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    logging_channel_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "System Control"
        verbose_name_plural = "System Control"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.set('maintenance_mode', self.is_maintenance, timeout=None)
        cache.set('read_only_mode', self.is_read_only, timeout=None)

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
    def set_state(cls, maintenance=None, read_only=None, user_id=None):
        obj, created = cls.objects.get_or_create(pk=1)
        if maintenance is not None:
            obj.is_maintenance = maintenance
        if read_only is not None:
            obj.is_read_only = read_only
        
        if user_id:
            obj.updated_by = str(user_id)
        obj.save()
        return obj
