from django import forms
from .models import Account, AccountAccess, Category, Goal

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'balance', 'account_number', 'monthly_budget']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['monthly_budget'].required = False
        
        if self.instance.pk:
            if 'balance' in self.fields: del self.fields['balance']
            if 'account_number' in self.fields: del self.fields['account_number']
            if 'monthly_budget' in self.fields: del self.fields['monthly_budget']

    def clean(self):
        cleaned_data = super().clean()
        if self.user and not self.instance.pk: # Only check on creation
            try:
                user_sub = self.user.subscription
            except Account.user.field.related_model.subscription.RelatedObjectDoesNotExist:
                # Emergency create subscription if missing
                from apps.subscriptions.models import SubscriptionPlan, UserSubscription
                basic_plan = SubscriptionPlan.objects.get(name='BASIC')
                user_sub = UserSubscription.objects.create(user=self.user, plan=basic_plan, status='ACTIVE')
            
            if user_sub.plan.max_accounts is not None:
                current_count = Account.objects.filter(user=self.user).count()
                if current_count >= user_sub.plan.max_accounts:
                    raise forms.ValidationError(
                        f"Your {user_sub.plan.get_name_display()} plan is limited to {user_sub.plan.max_accounts} account(s). Upgrade to add more."
                    )
        return cleaned_data

class AccountShareForm(forms.Form):
    email = forms.EmailField(label="User Email", required=True)
    level = forms.ChoiceField(
        choices=AccountAccess.ACCESS_LEVELS,
        label="Permission Level"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.user:
            user_sub = self.user.subscription
            # Check if sharing is allowed at all
            if not user_sub.plan.allow_shared_accounts:
                 raise forms.ValidationError(f"Your {user_sub.plan.get_name_display()} plan does not allow sharing accounts. Please upgrade.")

            # Check limit
            if user_sub.plan.max_shared_accounts is not None:
                current_shares = AccountAccess.objects.filter(account__user=self.user).count()
                # Note: This checks total shares across all accounts owned by user.
                # If we want per-account sharing limit, logic would differentiation.
                # Requirement says "Shared Users" limit normally implies total unique shares or total share instances.
                # Using total share instances for safety.
                if current_shares >= user_sub.plan.max_shared_accounts:
                    raise forms.ValidationError(
                        f"Your {user_sub.plan.get_name_display()} plan works with up to {user_sub.plan.max_shared_accounts} shared users. Upgrade to add more."
                    )
        return cleaned_data

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

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'target_amount', 'saved_amount', 'deadline']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }
