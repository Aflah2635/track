from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import SubscriptionPlan
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views import View

class PricingView(LoginRequiredMixin, ListView):
    model = SubscriptionPlan
    template_name = 'subscriptions/pricing.html'
    context_object_name = 'plans'

    def get_queryset(self):
        return SubscriptionPlan.objects.filter(is_active=True).order_by('price')

class SubscriptionSwitchView(LoginRequiredMixin, View):
    def post(self, request, pk):
        plan = get_object_or_404(SubscriptionPlan, pk=pk)
        
        # Mock Payment Logic - Just switch
        request.user.subscription.plan = plan
        request.user.subscription.save()

        # Enforce limits (unfreeze/freeze accounts)
        from apps.subscriptions.utils import enforce_subscription_limits
        enforce_subscription_limits(request.user)
        
        messages.success(request, f"Successfully switched to {plan.get_name_display()} Plan!")
        return redirect('dashboard')
