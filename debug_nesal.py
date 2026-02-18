import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Account
from apps.subscriptions.models import SubscriptionPlan
from apps.subscriptions.utils import enforce_subscription_limits

User = get_user_model()

def check_nesal():
    try:
        user = User.objects.get(username="Nesal")
    except User.DoesNotExist:
        print("User 'Nesal' not found.")
        return

    print(f"User: {user.username}")
    
    if hasattr(user, 'subscription'):
        print(f"Subscription Status: {user.subscription.status}")
        print(f"Plan: {user.subscription.plan.name}")
        print(f"Plan Max Accounts: {user.subscription.plan.max_accounts}")
    else:
        print("No subscription found.")

    accounts = Account.objects.filter(user=user).order_by('id')
    print("\nAccounts:")
    for acc in accounts:
        print(f" - ID: {acc.id} | Name: {acc.name} | Active: {acc.is_active}")

    print("\nRunning Enforcement Manually...")
    enforce_subscription_limits(user)
    
    print("\nRe-checking Accounts:")
    for acc in accounts:
        acc.refresh_from_db()
        print(f" - ID: {acc.id} | Name: {acc.name} | Active: {acc.is_active}")

if __name__ == "__main__":
    check_nesal()
