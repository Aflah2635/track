from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
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
        return Category.objects.filter(user=self.request.user)

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

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('category_list')

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
