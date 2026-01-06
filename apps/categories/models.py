from django.db import models
from django.conf import settings

class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Monthly budget limit")
    color = models.CharField(max_length=7, default="#3B82F6", help_text="HEX color for UI")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        unique_together = ['user', 'name']

    def __str__(self):
        return self.name
