import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Account
from apps.subscriptions.models import SubscriptionPlan, UserSubscription

User = get_user_model()

def setup_test_user():
    username = "test_pw_user"
    try:
        user = User.objects.get(username=username)
        user.delete()
        print(f"Deleted existing {username}")
    except User.DoesNotExist:
        pass

    user = User.objects.create_user(username=username, email="test@example.com", password="password123")
    
    # Ensure Basic Plan
    basic = SubscriptionPlan.objects.get(name='BASIC')
    sub, _ = UserSubscription.objects.get_or_create(user=user, defaults={'plan': basic})
    sub.plan = basic
    sub.save()

    # Create 2 accounts manually (bypassing view check)
    Account.objects.create(user=user, name="Account A - Active", balance=100)
    Account.objects.create(user=user, name="Account B - Should Freeze", balance=200)

    print(f"User {username} created with 2 accounts.")

if __name__ == "__main__":
    setup_test_user()
