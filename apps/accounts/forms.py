from django import forms
from .models import Account, AccountAccess, Category

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'balance']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            del self.fields['balance']

class AccountShareForm(forms.Form):
    email = forms.EmailField(label="User Email", required=True)
    level = forms.ChoiceField(
        choices=AccountAccess.ACCESS_LEVELS,
        label="Permission Level"
    )

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

    def clean_limit(self):
        limit = self.cleaned_data.get('limit')
        if limit is not None and limit < 0:
            raise forms.ValidationError("Limit cannot be negative.")
        return limit
