from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from apps.accounts.models import Account
from apps.transactions.models import Transaction
from decimal import Decimal

User = get_user_model()

class DashboardPerformanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.account = Account.objects.create(user=self.user, name='Test Account', balance=0)
        self.client = Client()
        self.client.login(username='testuser', password='password')
        self.url = reverse('dashboard') + f'?account={self.account.id}'

    def test_pagination(self):
        # Create 25 transactions
        objects = []
        for i in range(25):
            objects.append(Transaction(
                user=self.user,
                account=self.account,
                amount=Decimal('10.00'),
                type='DEBIT',
                title=f'Trans {i}'
            ))
        Transaction.objects.bulk_create(objects)
            
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Check that we have 20 items on page 1
        self.assertEqual(len(response.context['transactions']), 20)
        
        # Check page 2
        response = self.client.get(self.url + '&page=2')
        self.assertEqual(len(response.context['transactions']), 5)

    def test_caching_and_invalidation(self):
        # 1. Initial State
        cache_key = f'dashboard_stats_{self.account.id}'
        cache.delete(cache_key)
        
        # 2. Add transaction
        t = Transaction.objects.create(
            user=self.user,
            account=self.account,
            amount=Decimal('100.00'),
            type='CREDIT',
            title='Credit'
        )
        
        # 3. Load Dashboard -> Stats computed and Cached
        response = self.client.get(self.url)
        self.assertEqual(response.context['total_credit'], Decimal('100.00'))
        
        # Verify cache exists
        cached_stats = cache.get(cache_key)
        self.assertIsNotNone(cached_stats)
        self.assertEqual(cached_stats['total_credit'], Decimal('100.00'))
        
        # 4. Modify Transaction -> Cache Invalidated
        t.amount = Decimal('200.00')
        t.save() # Triggers signal/save method
        
        self.assertIsNone(cache.get(cache_key))
        
        # 5. Reload Dashboard -> New stats computed
        response = self.client.get(self.url)
        self.assertEqual(response.context['total_credit'], Decimal('200.00'))
        
        # 6. Delete Transaction -> Cache Invalidated
        t.delete() # Triggers delete method
        self.assertIsNone(cache.get(cache_key))
