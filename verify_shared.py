import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Account, AccountAccess

User = get_user_model()

def verify_is_shared():
    # Create two users
    user1, _ = User.objects.get_or_create(username='user1_test', email='u1@test.com', password='password')
    user2, _ = User.objects.get_or_create(username='user2_test', email='u2@test.com', password='password')

    # Create an account for user1
    account = Account.objects.create(user=user1, name='Test Account')
    
    print(f"Account created. Owner: {account.user.username}")
    print(f"Is Shared (Initial): {account.is_shared}")

    # Share with user2
    AccountAccess.objects.create(account=account, user=user2, level='VIEW')
    
    # Refresh from db isn't strictly necessary for property but good to be same instance type logic
    # The property uses self.shared_users.exists() which hits DB.
    print(f"Account shared with {user2.username}")
    print(f"Is Shared (After Sharing): {account.is_shared}")
    
    # Clean up
    account.delete()
    user1.delete()
    user2.delete()

if __name__ == '__main__':
    try:
        verify_is_shared()
        print("Verification Successful!")
    except Exception as e:
        print(f"Verification Failed: {e}")
