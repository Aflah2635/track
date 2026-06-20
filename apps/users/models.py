from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_frozen = models.BooleanField(default=False, help_text="Designates whether this user has been frozen.")
    force_logout_time = models.DateTimeField(null=True, blank=True, help_text="If set, user will be forced to logout if their session started before this time.")
    is_verified = models.BooleanField(default=False, help_text="Designates whether this user has verified their email address.")

    
    def __str__(self):
        return self.username

class LoginActivity(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='login_history')
    login_datetime = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('SUCCESS', 'Success'), ('FAILED', 'Failed')], default='SUCCESS')

    class Meta:
        ordering = ['-login_datetime']

    def __str__(self):
        return f"{self.user.username} - {self.status} at {self.login_datetime}"
