import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.subscriptions.utils import enforce_subscription_limits

User = get_user_model()

def fix_all():
    print("Starting global account limit enforcement...")
    users = User.objects.all()
    count = 0
    for user in users:
        try:
            enforce_subscription_limits(user)
            print(f"Fixed/Checked user: {user.username}")
            count += 1
        except Exception as e:
            print(f"Error checking user {user.username}: {e}")
            
    print(f"Finished. Processed {count} users.")

if __name__ == "__main__":
    fix_all()
