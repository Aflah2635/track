from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model

from apps.users.forms import CustomUserCreationForm, CustomUserChangeForm
from apps.accounts.models import Account, Category
from apps.core.models import MaintenanceState
from apps.notifications.models import Notification, Broadcast
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from .forms import UserSubscriptionForm

User = get_user_model()

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'custom_admin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['total_accounts'] = Account.objects.count()
        return context

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'custom_admin/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    ordering = ['-date_joined']

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'custom_admin/user_form.html'
    success_url = reverse_lazy('custom_admin:user_list')

class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'custom_admin/user_form.html'
    success_url = reverse_lazy('custom_admin:user_list')

class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'custom_admin/user_confirm_delete.html'
    success_url = reverse_lazy('custom_admin:user_list')



# --- Accounts ---
class AccountListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Account
    template_name = 'custom_admin/account_list.html'
    context_object_name = 'accounts'
    paginate_by = 20
    ordering = ['-created_at']

class AccountCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Account
    fields = ['user', 'name', 'balance', 'monthly_budget', 'account_number', 'is_active']
    template_name = 'custom_admin/generic_form.html'
    success_url = reverse_lazy('custom_admin:account_list')
    extra_context = {'title': 'Add Account', 'subtitle': 'Create a new user account.'}

class AccountUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Account
    fields = ['user', 'name', 'balance', 'monthly_budget', 'account_number', 'is_active']
    template_name = 'custom_admin/generic_form.html'
    success_url = reverse_lazy('custom_admin:account_list')
    extra_context = {'title': 'Edit Account', 'subtitle': 'Update account details.'}

class AccountDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Account
    template_name = 'custom_admin/generic_confirm_delete.html'
    success_url = reverse_lazy('custom_admin:account_list')
    extra_context = {'object_type': 'Account'}

# --- Categories ---
class CategoryListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Category
    template_name = 'custom_admin/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    ordering = ['name']

class CategoryCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Category
    fields = ['user', 'account', 'name', 'limit', 'color']
    template_name = 'custom_admin/generic_form.html'
    success_url = reverse_lazy('custom_admin:category_list')
    extra_context = {'title': 'Add Category', 'subtitle': 'Create a new transaction category.'}

class CategoryUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Category
    fields = ['user', 'account', 'name', 'limit', 'color']
    template_name = 'custom_admin/generic_form.html'
    success_url = reverse_lazy('custom_admin:category_list')
    extra_context = {'title': 'Edit Category', 'subtitle': 'Update category details.'}

class CategoryDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Category
    template_name = 'custom_admin/generic_confirm_delete.html'
    success_url = reverse_lazy('custom_admin:category_list')
    extra_context = {'object_type': 'Category'}

# --- Subscriptions ---
class SubscriptionPlanListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = SubscriptionPlan
    template_name = 'custom_admin/subscription_plan_list.html'
    context_object_name = 'plans'
    ordering = ['price']

class SubscriptionPlanCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = SubscriptionPlan
    fields = '__all__'
    template_name = 'custom_admin/generic_form.html'
    success_url = reverse_lazy('custom_admin:plan_list')
    extra_context = {'title': 'Add Plan', 'subtitle': 'Create a new subscription plan.'}

class SubscriptionPlanUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = SubscriptionPlan
    fields = '__all__'
    template_name = 'custom_admin/generic_form.html'
    success_url = reverse_lazy('custom_admin:plan_list')
    extra_context = {'title': 'Edit Plan', 'subtitle': 'Update subscription plan.'}

class SubscriptionPlanDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = SubscriptionPlan
    template_name = 'custom_admin/generic_confirm_delete.html'
    success_url = reverse_lazy('custom_admin:plan_list')
    extra_context = {'object_type': 'Subscription Plan'}

class UserSubscriptionListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = UserSubscription
    template_name = 'custom_admin/user_subscription_list.html'
    context_object_name = 'user_subscriptions'
    ordering = ['-start_date']

class UserSubscriptionCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = UserSubscription
    form_class = UserSubscriptionForm
    template_name = 'custom_admin/generic_form.html'
    success_url = reverse_lazy('custom_admin:user_subscription_list')
    extra_context = {'title': 'Add User Subscription', 'subtitle': 'Assign a plan to a user.'}

class UserSubscriptionUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = UserSubscription
    form_class = UserSubscriptionForm
    template_name = 'custom_admin/generic_form.html'
    success_url = reverse_lazy('custom_admin:user_subscription_list')
    extra_context = {'title': 'Edit User Subscription', 'subtitle': 'Update subscription details.'}

class UserSubscriptionDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = UserSubscription
    template_name = 'custom_admin/generic_confirm_delete.html'
    success_url = reverse_lazy('custom_admin:user_subscription_list')
    extra_context = {'object_type': 'User Subscription'}

# --- Notifications ---
class NotificationListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Notification
    template_name = 'custom_admin/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    ordering = ['-created_at']

class BroadcastCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Broadcast
    fields = ['message', 'type']
    template_name = 'custom_admin/generic_form.html'
    success_url = reverse_lazy('custom_admin:notification_list') # Redirect to list after broadcast
    extra_context = {'title': 'New Broadcast', 'subtitle': 'Send a mass notification to all users.', 'submit_text': 'Send Broadcast'}

    def form_valid(self, form):
        # Here we would actually trigger the broadcast logic
        # For now just saving the record
        response = super().form_valid(form)
        # Logic to create Notifications for all users could go here
        # self.object.send_broadcast() # Hypothetical method
        return response

class NotificationDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Notification
    template_name = 'custom_admin/generic_confirm_delete.html'
    success_url = reverse_lazy('custom_admin:notification_list')
    extra_context = {'object_type': 'Notification'}

# --- Core (System Control) ---
class MaintenanceStateUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = MaintenanceState
    fields = ['is_maintenance', 'is_read_only', 'logging_channel_id']
    template_name = 'custom_admin/generic_form.html'
    success_url = reverse_lazy('custom_admin:dashboard')
    extra_context = {'title': 'System Control', 'subtitle': 'Manage maintenance and read-only modes.'}

    def get_object(self, queryset=None):
        obj, created = MaintenanceState.objects.get_or_create(pk=1)
        return obj
