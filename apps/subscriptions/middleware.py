from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from apps.accounts.models import Account, AccountAccess
from apps.subscriptions.models import UserSubscription, SubscriptionPlan
from django.utils import timezone

class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                # Try to access the subscription
                sub = request.user.subscription
                
                # Check for Expiry
                if sub.plan.name != 'BASIC' and sub.end_date and sub.end_date < timezone.now():
                    # Downgrade immediately
                    basic_plan = SubscriptionPlan.objects.get(name='BASIC')
                    sub.plan = basic_plan
                    sub.status = 'EXPIRED'
                    sub.end_date = None # Basic has no end date
                    sub.save()
                    
                    # Enforce limits (freeze accounts if needed)
                    from apps.subscriptions.utils import enforce_subscription_limits
                    enforce_subscription_limits(request.user)
                    
                    messages.warning(request, "Your subscription has expired and you have been downgraded to the Basic plan.")

            except ObjectDoesNotExist:
                # Self-healing: Create default subscription if missing
                basic_plan = SubscriptionPlan.objects.get(name='BASIC')
                sub = UserSubscription.objects.create(
                    user=request.user,
                    plan=basic_plan,
                    status='ACTIVE'
                )
                # Invalidate cache to ensure subsequent access works
                if hasattr(request.user, '_subscription_cache'):
                    del request.user._subscription_cache

            # Attach plan for easy access in templates/views
            request.user_subscription = getattr(request.user, 'subscription', None) # Safely get
            request.user_plan = getattr(request.user_subscription, 'plan', None)
        else:
            request.user_subscription = None
            request.user_plan = None

        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated or not getattr(request, 'user_plan', None):
            return None

        url_name = request.resolver_match.url_name
        plan = request.user_plan

        # 1. Enforce Account Creation Limit
        if url_name == 'create_account' and request.method == 'POST':
            if plan.max_accounts is not None:
                current_count = Account.objects.filter(user=request.user).count()
                if current_count >= plan.max_accounts:
                    messages.error(request, f"Plan limit reached ({plan.max_accounts} accounts). Upgrade to create more.")
                    return redirect('pricing')

        # 2. Enforce Shared Account Limit
        if url_name == 'share_account' and request.method == 'POST':
            if plan.max_shared_accounts is not None:
                # Get current shares count
                # Count distinct users this user has shared WITH across all their owned accounts
                # Wait, "max_shared_accounts" means "How many accounts I can share" OR "How many users I can share with"?
                # Prompt says "Shared accounts (invite users)". 
                # Let's interpret as: "Total number of successful shares (AccountAccess records) on my owned accounts".
                current_shares = AccountAccess.objects.filter(account__user=request.user).count()
                if current_shares >= plan.max_shared_accounts:
                    messages.error(request, f"Plan limit reached ({plan.max_shared_accounts} shared users/accounts). Upgrade to share more.")
                    return redirect('pricing')

        # 3. Enforce Export Limit (If user tries to access export URL and plan forbids it)
        # Note: We haven't implemented a generic "export" view yet, but if we did:
        if 'export' in url_name and not plan.allow_export:
             messages.error(request, "Exporting data is available on Plus/Pro plans.")
             return redirect('pricing')
             
        # 4. Enforce Analytics (If user tries to access analytics URL - not yet existing but good to have)
        if 'analytics' in url_name and not plan.allow_advanced_analytics:
             messages.error(request, "Advanced Analytics is available on Plus/Pro plans.")
             return redirect('pricing')

        return None
