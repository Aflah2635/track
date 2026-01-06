from django import forms
from .models import Transaction
from apps.accounts.models import Account

from django.db.models import Q
from apps.accounts.models import AccountAccess

from apps.categories.models import Category

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'type', 'account', 'category', 'amount', 'description', 'counterparty']
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Owned accounts
        owned = Account.objects.filter(user=user)
        # Shared accounts with ADD or FULL access
        shared_ids = AccountAccess.objects.filter(
            user=user, 
            level__in=['ADD', 'FULL']
        ).values_list('account_id', flat=True)
        shared = Account.objects.filter(id__in=shared_ids)
        
        self.fields['account'].queryset = (owned | shared).distinct()
        self.fields['category'].queryset = Category.objects.filter(user=user)
