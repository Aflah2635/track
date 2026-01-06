from django import forms
from .models import Account, AccountAccess

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'balance']

class AccountShareForm(forms.Form):
    email = forms.EmailField(label="User Email", required=True)
    level = forms.ChoiceField(
        choices=AccountAccess.ACCESS_LEVELS,
        label="Permission Level"
    )
