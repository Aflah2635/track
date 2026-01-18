from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.users.models import LoginActivity
from django.urls import reverse

User = get_user_model()

class SecurityFeaturesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123', email='test@example.com')
        self.client = Client()

    def test_login_activity_logging_success(self):
        login_url = reverse('login')
        response = self.client.post(login_url, {'username': 'testuser', 'password': 'password123'})
        self.assertEqual(response.status_code, 302) # Should redirect
        
        # Check if LoginActivity was created
        activity = LoginActivity.objects.filter(user=self.user).first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.status, 'SUCCESS')
        
    def test_login_activity_logging_failure(self):
        login_url = reverse('login')
        response = self.client.post(login_url, {'username': 'testuser', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200) # Form error
        
        # Check if LoginActivity was created
        activity = LoginActivity.objects.filter(user=self.user, status='FAILED').first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.status, 'FAILED')

    def test_security_settings_view(self):
        self.client.login(username='testuser', password='password123')
        url = reverse('security_settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Security Settings')
        # Check context
        self.assertTrue('login_history' in response.context)
        self.assertTrue(len(response.context['login_history']) > 0)

    def test_global_logout(self):
        self.client.login(username='testuser', password='password123')
        # Create a dummy session or assume login created one.
        # We can't easily test "other sessions" with Django test client in one go without creating session objects manually,
        # but we can test that the current one is logged out.
        
        url = reverse('global_logout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) # Redirects to login
        
        # Check if logged out
        response = self.client.get(reverse('dashboard')) # protected page
        self.assertNotEqual(response.status_code, 200) # Should be redirect to login
