from apps.accounts.models import Account
from apps.subscriptions.models import SubscriptionPlan

def enforce_subscription_limits(user):
    """
    Enforces subscription limits on user's accounts.
    - Activates accounts up to the plan's max_accounts limit.
    - Deactivates (freezes) any accounts exceeding the limit.
    - If max_accounts is None (unlimited), activates all accounts.
    """
    if not hasattr(user, 'subscription'):
        return

    # Ensure we have the latest plan data
    try:
        user.subscription.refresh_from_db()
    except Exception:
        return

    plan = user.subscription.plan
    max_accounts = plan.max_accounts
    
    # print(f"Enforcing limits for {user.username}: Plan={plan.name}, Max={max_accounts}")

    # Get all accounts ordered by ID (creation order)
    accounts = Account.objects.filter(user=user).order_by('id')

    if max_accounts is None:
        # Unlimited: Activate all
        accounts.update(is_active=True)
    else:
        # Limit exists: Activate first N, deactivate rest
        for index, account in enumerate(accounts):
            if index < max_accounts:
                if not account.is_active:
                    account.is_active = True
                    account.save()
            else:
                if account.is_active:
                    account.is_active = False
                    account.save()
