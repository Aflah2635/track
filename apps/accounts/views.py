from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Account, AccountAccess
from .forms import AccountForm, AccountShareForm

class AccountCreateView(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Check subscription limits
        user = self.request.user
        if hasattr(user, 'subscription'):
            plan = user.subscription.plan
            if plan.max_accounts is not None:
                current_count = Account.objects.filter(user=user).count()
                if current_count >= plan.max_accounts:
                    messages.error(self.request, f"Your {plan.name} plan is limited to {plan.max_accounts} account(s). Upgrade to create more.")
                    return redirect('pricing')

        form.instance.user = self.request.user
        messages.success(self.request, f"Account '{form.instance.name}' created successfully!")
        return super().form_valid(form)

from apps.subscriptions.decorators import plan_required

@login_required
@plan_required('allow_shared_accounts')
def share_account(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = AccountShareForm(request.POST, user=request.user)
        if form.is_valid():
            email = form.cleaned_data['email']
            level = form.cleaned_data['level']
            User = get_user_model()
            
            try:
                user_to_share = User.objects.get(email=email)
                if user_to_share == request.user:
                    messages.error(request, "You cannot share an account with yourself.")
                else:
                    # Create or update access
                    access, created = AccountAccess.objects.update_or_create(
                        account=account,
                        user=user_to_share,
                        defaults={'level': level}
                    )
                    messages.success(request, f"Account shared with {user_to_share.username} ({level}).")
                    return redirect('dashboard')
            except User.DoesNotExist:
                messages.error(request, "User with this email does not exist.")
    else:
        form = AccountShareForm(user=request.user)
    
    # Get current shared users
    shared_users = account.shared_users.select_related('user').all()
    
    return render(request, 'accounts/share_account.html', {
        'account': account,
        'form': form,
        'shared_users': shared_users
    })

@login_required
def revoke_access(request, pk, user_id):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    try:
        access = AccountAccess.objects.get(account=account, user_id=user_id)
        shared_username = access.user.username
        access.delete()
        messages.success(request, f"Access revoked for {shared_username}.")
    except AccountAccess.DoesNotExist:
        messages.error(request, "Access record not found.")
    
    return redirect('share_account', pk=pk)

from django.views.generic import ListView, UpdateView, DeleteView

class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    template_name = 'accounts/manage_accounts.html'
    context_object_name = 'owned_accounts'
    
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add shared accounts to context
        shared_ids = AccountAccess.objects.filter(user=self.request.user).values_list('account_id', flat=True)
        context['shared_accounts'] = Account.objects.filter(id__in=shared_ids)
        return context

class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('manage_accounts')
    
    def get_queryset(self):
        # Only allow editing owned accounts
        return Account.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f"Account '{form.instance.name}' updated successfully!")
        return super().form_valid(form)

class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = Account
    template_name = 'accounts/account_confirm_delete.html'
    success_url = reverse_lazy('manage_accounts')
    
    def get_queryset(self):
        # Only allow deleting owned accounts
        return Account.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        account = self.get_object()
        from apps.audit.utils import log_to_discord, LogEvents, LogColors
        
        log_to_discord(
            LogEvents.ACCOUNT_DELETED,
            "Account Deleted",
            request.user,
            {
                "Account": account.name,
                "Balance": str(account.balance),
                "Reason": "User Request"
            },
            LogColors.ERROR,
            "🗑️"
        )
        messages.success(self.request, "Account deleted successfully.")
        return super().delete(request, *args, **kwargs)

# Category Views
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Category
from .forms import CategoryForm
from apps.transactions.models import Transaction

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'categories/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        user = self.request.user
        account_id = self.request.GET.get('account')
        
        if account_id:
            # Check if user has access to this account
            has_access = Account.objects.filter(id=account_id, user=user).exists()
            if not has_access:
                has_access = AccountAccess.objects.filter(account_id=account_id, user=user).exists()
            
            if has_access:
                # Show:
                # 1. Own global categories (user=user, account=None)
                # 2. Categories linked to this account (account_id=account_id) - regardless of owner
                return Category.objects.filter(
                    Q(user=user, account__isnull=True) | 
                    Q(account_id=account_id)
                ).distinct()
        
        # Fallback (All own categories)
        qs = Category.objects.filter(user=user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        categories = context['categories']
        for category in categories:
            # Calculate spent amount for this category in current month
            spent = Transaction.objects.filter(
                user=self.request.user,
                category=category,
                timestamp__gte=start_of_month,
                type__in=['DEBIT', 'LEND'] # Assuming these reduce budget
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            category.spent = spent
            if category.limit > 0:
                percent_val = min((spent / category.limit) * 100, 100)
                category.percent = int(round(percent_val))
            else:
                category.percent = 0
                
        return context

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('category_list')

    def get_initial(self):
        initial = super().get_initial()
        if 'account' in self.request.GET:
            initial['account'] = self.request.GET.get('account')
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, f"Category '{form.instance.name}' created.")
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('category_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"Category '{form.instance.name}' updated.")
        return super().form_valid(form)

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Category deleted successfully.")
        return super().delete(request, *args, **kwargs)

@login_required
def switch_account(request, pk):
    """
    Switch the active account for the dashboard.
    Verifies that the user has access to the account before switching.
    """
    if request.method == 'POST':
        # Check if owned
        is_owned = Account.objects.filter(id=pk, user=request.user).exists()
        
        # Check if shared
        is_shared = AccountAccess.objects.filter(account_id=pk, user=request.user).exists()
        
        if is_owned or is_shared:
            # Check if account is active (frozen check)
            account = Account.objects.get(id=pk)
            if not account.is_active:
                messages.error(request, "This account is frozen due to subscription limits. Upgrade to unlock.")
                return redirect('dashboard')

            request.session['active_account_id'] = pk
            messages.success(request, f"Switched account successfully.")
        else:
            messages.error(request, "You do not have access to this account.")
            
    return redirect('dashboard')

from .models import Goal
from .forms import GoalForm

class GoalCreateView(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'accounts/goal_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, f"Goal '{form.instance.name}' created.")
        return super().form_valid(form)

class GoalUpdateView(LoginRequiredMixin, UpdateView):
    model = Goal
    form_class = GoalForm
    template_name = 'accounts/goal_form.html'
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"Goal '{form.instance.name}' updated.")
        return super().form_valid(form)

class GoalDeleteView(LoginRequiredMixin, DeleteView):
    model = Goal
    template_name = 'accounts/goal_confirm_delete.html'
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Goal deleted successfully.")
        return super().delete(request, *args, **kwargs)
