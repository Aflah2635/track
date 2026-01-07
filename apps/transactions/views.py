from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q
from .models import Transaction
from .forms import TransactionForm
from django.shortcuts import redirect

import json
from django.core.serializers.json import DjangoJSONEncoder

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/transaction_form.html'

    def get_success_url(self):
        url = reverse_lazy('dashboard')
        if self.object.account:
            return f"{url}?account={self.object.account.id}"
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' in context:
            categories = context['form'].fields['category'].queryset
        else:
            # Fallback if form not in context (shouldn't happen in CreateView usually)
            # Actually CreateView passes form.
            # But let's be safe or just use self.get_form_class()(user=self.request.user) ? No too heavy.
            # CreateView calls get_context_data with form=form.
            categories = self.get_form_kwargs()['user'].categories.all() # Fallback
            
        cat_map = {}
        for cat in categories:
            cat_map[cat.id] = cat.account_id if cat.account_id else 'global'
        context['category_account_map'] = json.dumps(cat_map, cls=DjangoJSONEncoder)
        return context

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
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/transaction_form.html'
    
    def get_success_url(self):
        url = reverse_lazy('dashboard')
        if self.object.account:
            return f"{url}?account={self.object.account.id}"
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = self.get_form_kwargs()['user'].categories.all()
        cat_map = {}
        for cat in categories:
            cat_map[cat.id] = cat.account_id if cat.account_id else 'global'
        context['category_account_map'] = json.dumps(cat_map, cls=DjangoJSONEncoder)
        return context

    def get_queryset(self):
        # Allow editing if user owns the account OR has ADD/FULL access
        return Transaction.objects.filter(
            Q(account__user=self.request.user) |
            Q(account__shared_users__user=self.request.user, account__shared_users__level__in=['ADD', 'FULL'])
        ).distinct()

    def form_valid(self, form):
        form.instance.last_modified_by = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'transactions/transaction_confirm_delete.html'
    
    def get_success_url(self):
        url = reverse_lazy('dashboard')
        if self.object.account:
            return f"{url}?account={self.object.account.id}"
        return url

    def get_queryset(self):
        # Allow deleting if user owns the account OR has FULL access
        return Transaction.objects.filter(
            Q(account__user=self.request.user) |
            Q(account__shared_users__user=self.request.user, account__shared_users__level='FULL')
        ).distinct()
