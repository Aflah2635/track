from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q
from .models import Transaction
from .forms import TransactionForm
from django.shortcuts import redirect

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/transaction_form.html'
    success_url = reverse_lazy('dashboard')

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
    success_url = reverse_lazy('dashboard')

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
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        # Allow deleting if user owns the account OR has FULL access
        return Transaction.objects.filter(
            Q(account__user=self.request.user) |
            Q(account__shared_users__user=self.request.user, account__shared_users__level='FULL')
        ).distinct()
