from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Category
from .forms import CategoryForm
from apps.transactions.models import Transaction

from apps.accounts.models import Account, AccountAccess

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

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
