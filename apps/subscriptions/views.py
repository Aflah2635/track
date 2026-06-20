from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import SubscriptionPlan
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from apps.notifications.utils import send_tracked_email

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
        
        # Send Premium Purchase Confirmation if upgrading to Plus/Pro
        if plan.name in ['PLUS', 'PRO']:
            context = {
                'user': request.user,
                'plan': plan,
                'subscription': request.user.subscription,
                'manage_url': request.build_absolute_uri('/subscriptions/')
            }
            send_tracked_email(
                email_type='PREMIUM_PURCHASE',
                subject='Premium Subscription Activated',
                template_name='premium_purchase',
                context=context,
                recipient_list=[request.user.email],
                user=request.user
            )

        messages.success(request, f"Successfully switched to {plan.get_name_display()} Plan!")
        return redirect('dashboard')
