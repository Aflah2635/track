from django import forms
from .models import Category
from apps.accounts.models import Account, AccountAccess

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'account', 'limit', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Owned accounts
            owned = Account.objects.filter(user=self.user)
            # Shared accounts with ADD/FULL access
            shared_ids = AccountAccess.objects.filter(
                user=self.user, 
                level__in=['ADD', 'FULL']
            ).values_list('account_id', flat=True)
            shared = Account.objects.filter(id__in=shared_ids)
            
            self.fields['account'].queryset = (owned | shared).distinct()
            self.fields['account'].required = False
            self.fields['account'].label = "Account (Optional - Leave blank for Global)"
