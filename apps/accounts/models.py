from django.db import models
from django.conf import settings

class Account(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    monthly_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Monthly budget limit")
    account_number = models.CharField(max_length=30, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

class AccountAccess(models.Model):
    ACCESS_LEVELS = [
        ('VIEW', 'Viewer (Read Only)'),
        ('ADD', 'Editor (Add/Edit Transactions)'),
        ('FULL', 'Full Control'),
    ]
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='shared_users')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_accounts')
    level = models.CharField(max_length=10, choices=ACCESS_LEVELS, default='VIEW')
    
    class Meta:
        unique_together = ('account', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.account.name} ({self.level})"
