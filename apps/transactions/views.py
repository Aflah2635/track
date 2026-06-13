from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q
from .models import Transaction
from .forms import TransactionForm
from .forms import TransactionForm
from django.shortcuts import redirect
from django.contrib import messages

import json
from django.core.serializers.json import DjangoJSONEncoder

from django.views.generic import ListView
from django.db.models import Q

from apps.accounts.models import Account, Category

class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        # Allow viewing if user owns the account OR has any shared access
        qs = Transaction.objects.filter(
            Q(account__user=self.request.user) |
            Q(account__shared_users__user=self.request.user)
        ).select_related('account', 'category', 'created_by').order_by('-timestamp')
        
        # Filtering
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(amount__icontains=query)
            )
            
        account_id = self.request.GET.get('account')
        if account_id:
            qs = qs.filter(account_id=account_id)
            
        category_id = self.request.GET.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
            
        date_from = self.request.GET.get('date_from')
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)
            
        date_to = self.request.GET.get('date_to')
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)
            
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass accounts and categories for filter dropdowns
        context['accounts'] = Account.objects.filter(
            Q(user=self.request.user) | 
            Q(shared_users__user=self.request.user)
        ).distinct()
        
        context['categories'] = Category.objects.filter(
            Q(user=self.request.user) |
            Q(account__user=self.request.user) |
            Q(account__shared_users__user=self.request.user)
        ).distinct()
        
        return context

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
            
        # Settlement Logic
        settle_id = self.request.GET.get('settle')
        if settle_id:
            try:
                original = Transaction.objects.get(pk=settle_id, user=self.request.user)
                initial['title'] = f"Settlement: {original.title}"
                initial['amount'] = original.amount
                initial['account'] = original.account
                initial['category'] = original.category
                initial['counterparty'] = original.counterparty
                
                # Reverse type
                if original.type == 'LEND':
                    initial['type'] = 'CREDIT' # Money coming back
                elif original.type == 'BORROW':
                    initial['type'] = 'DEBIT' # Money going out
            except Transaction.DoesNotExist:
                pass
                
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.created_by = self.request.user
        messages.success(self.request, "Transaction added successfully.")
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
        messages.success(self.request, "Transaction updated successfully.")
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

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Transaction deleted successfully.")
        return super().delete(request, *args, **kwargs)

from django.http import HttpResponse
from apps.subscriptions.decorators import plan_required
from django.utils.decorators import method_decorator
from django.views import View
import csv
import openpyxl
from datetime import datetime

@method_decorator(plan_required('allow_export'), name='dispatch')
class ExportTransactionsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # 1. Get filtered queryset (Same logic as TransactionListView)
        qs = Transaction.objects.filter(
            Q(account__user=self.request.user) |
            Q(account__shared_users__user=self.request.user)
        ).select_related('account', 'category', 'created_by').order_by('-timestamp')
        
        # Apply filters
        query = request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(amount__icontains=query)
            )
            
        account_id = request.GET.get('account')
        if account_id:
            qs = qs.filter(account_id=account_id)
            
        category_id = request.GET.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
            
        date_from = request.GET.get('date_from')
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)
            
        date_to = request.GET.get('date_to')
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)
            
        export_format = request.GET.get('format', 'csv')
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        
        if export_format == 'xlsx':
            return self.export_excel(qs, timestamp)
        else:
            return self.export_csv(qs, timestamp)

    def export_csv(self, qs, timestamp):
        from django.http import StreamingHttpResponse
        
        class Echo:
            """An object that implements just the write method of the file-like interface."""
            def write(self, value):
                """Write the value by returning it, instead of storing in a buffer."""
                return value

        def stream_rows():
            buffer = Echo()
            writer = csv.writer(buffer)
            # Yield BOM
            yield '\ufeff'
            # Yield Header
            yield writer.writerow(['Date', 'Title', 'Amount', 'Type', 'Category', 'Account', 'Counterparty'])
            
            from django.utils.timezone import localtime
            for t in qs:
                yield writer.writerow([
                    localtime(t.timestamp).strftime('%Y-%m-%d'), 
                    t.title, 
                    t.amount, 
                    t.type, 
                    t.category.name if t.category else 'Uncategorized', 
                    t.account.name,
                    t.counterparty
                ])

        response = StreamingHttpResponse(stream_rows(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="transactions_{timestamp}.csv"'
        return response

    def export_excel(self, qs, timestamp):
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="transactions_{timestamp}.xlsx"'
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Transactions"
        
        # Headers
        headers = ['Date', 'Title', 'Amount', 'Type', 'Category', 'Account', 'Counterparty']
        ws.append(headers)
        
        # Styling headers
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)
        
        from django.utils.timezone import localtime
        for t in qs:
            row = [
                localtime(t.timestamp).date(), # Export as Date object so Excel formats it as Short Date
                t.title,
                t.amount,
                t.type,
                t.category.name if t.category else 'Uncategorized',
                t.account.name,
                t.counterparty
            ]
            ws.append(row)
            
        wb.save(response)
        return response
