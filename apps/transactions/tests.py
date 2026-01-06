from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.models import Account
from apps.transactions.models import Transaction

User = get_user_model()

class TransactionLogicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123', email='test@example.com')
        self.account = Account.objects.create(user=self.user, name='Main Bank', balance=1000.00)

    def test_credit_transaction(self):
        """Test CREDIT increases balance"""
        txn = Transaction.objects.create(
            user=self.user,
            account=self.account,
            title='Salary Credit',
            type='CREDIT',
            amount=500.00,
            description='Salary'
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 1500.00) # 1000 + 500

    def test_view_logic(self):
        """Test the logic via the View/Client"""
        self.client.login(username='testuser', password='password123')
        
        # Initial balance 1000
        response = self.client.post('/transaction/new/', {
            'title': 'Grocery Shopping',
            'type': 'DEBIT',
            'account': self.account.id,
            'amount': 100.00,
            'description': 'Groceries',
            'counterparty': ''
        })
        self.assertEqual(response.status_code, 302) # Redirects to dashboard
        
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 900.00) # 1000 - 100

        # Credit
        self.client.post('/transaction/new/', {
            'title': 'Refund Received',
            'type': 'CREDIT',
            'account': self.account.id,
            'amount': 200.00,
            'description': 'Refund',
            'counterparty': ''
        })
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 1100.00)
