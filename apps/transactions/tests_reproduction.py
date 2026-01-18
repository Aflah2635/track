from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.models import Account
from apps.transactions.models import Transaction

User = get_user_model()

class TransactionUpdateBugTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testbug', password='password123', email='testbug@example.com')
        self.account = Account.objects.create(user=self.user, name='Buggy Bank', balance=1000.00)

    def test_update_transaction_balance(self):
        """Test that updating a transaction correctly adjusts balance"""
        # 1. Create Initial Transaction (DEBIT 100)
        txn = Transaction.objects.create(
            user=self.user,
            account=self.account,
            title='Test Debit',
            type='DEBIT',
            amount=100.00
        )
        
        self.account.refresh_from_db()
        # Balance should be 1000 - 100 = 900
        self.assertEqual(self.account.balance, 900.00, "Initial balance incorrect")

        # 2. Update Transaction (Change amount to 200)
        # We simulate what the View does: load instance, change fields, save.
        txn.amount = 200.00
        txn.save()
        
        self.account.refresh_from_db()
        print(f"DEBUG: Balance is {self.account.balance}")
        # Expected: 900 + 100 (reversal of old) - 200 (new) = 800
        # If user says "add to balance again", maybe it's doing something else.
        self.assertEqual(self.account.balance, 800.00, f"Balance after update incorrect. Got {self.account.balance}")
