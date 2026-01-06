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

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, f"Account '{form.instance.name}' created successfully!")
        return super().form_valid(form)

@login_required
def share_account(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = AccountShareForm(request.POST)
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
        form = AccountShareForm()
    
    # Get current shared users
    shared_users = account.shared_users.select_related('user').all()
    
    return render(request, 'accounts/share_account.html', {
        'account': account,
        'form': form,
        'shared_users': shared_users
    })

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
        messages.success(self.request, "Account deleted successfully.")
        return super().delete(request, *args, **kwargs)
