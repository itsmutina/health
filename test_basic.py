#!/usr/bin/env python
"""
Basic tests for Mental Health Journal Django application.
Run with: python test_basic.py
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental_health_journal.settings')
django.setup()

User = get_user_model()

class BasicTests(TestCase):
    """Basic functionality tests."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_landing_page(self):
        """Test that landing page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mental Health Journal')
    
    def test_login_page(self):
        """Test that login page loads."""
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome Back')
    
    def test_signup_page(self):
        """Test that signup page loads."""
        response = self.client.get('/accounts/signup/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')
    
    def test_home_redirect_when_not_logged_in(self):
        """Test that home page redirects when not logged in."""
        response = self.client.get('/app/')
        self.assertRedirects(response, '/accounts/login/?next=/app/')
    
    def test_home_when_logged_in(self):
        """Test that home page loads when logged in."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/app/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome back')
    
    def test_new_entry_page(self):
        """Test that new entry page loads when logged in."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/app/entry/new/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Log Today\'s Entry')
    
    def test_settings_page(self):
        """Test that settings page loads when logged in."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/accounts/settings/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Settings')
    
    def test_insights_page(self):
        """Test that insights page loads when logged in."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/insights/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Insights & Analytics')
    
    def test_reports_page(self):
        """Test that reports page loads when logged in."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reports')

def run_tests():
    """Run all tests."""
    print("Running basic tests for Mental Health Journal...")
    print("=" * 50)
    
    # Run tests
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["__main__"])
    
    if failures:
        print(f"\n✗ {failures} test(s) failed")
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")

if __name__ == '__main__':
    run_tests()
