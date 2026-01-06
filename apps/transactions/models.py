from django.db import models
from django.conf import settings
from apps.accounts.models import Account
from apps.categories.models import Category

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
        ('LEND', 'Lend'),
        ('BORROW', 'Borrow'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_transactions')
    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Store name of person involved in lending/borrowing if applicable
    counterparty = models.CharField(max_length=100, blank=True, help_text="Person you lent to or borrowed from")
    
    def __str__(self):
        return f"{self.type} - {self.amount} - {self.timestamp}"

    def save(self, *args, **kwargs):
        from django.core.cache import cache
        super().save(*args, **kwargs)
        # Invalidate dashboard stats cache for this account
        if self.account_id:
            cache.delete(f'dashboard_stats_{self.account_id}')

    def delete(self, *args, **kwargs):
        from django.core.cache import cache
        account_id = self.account_id
        super().delete(*args, **kwargs)
        if account_id:
            cache.delete(f'dashboard_stats_{account_id}')
