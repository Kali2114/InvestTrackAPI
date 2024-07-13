"""
Tests for models.
"""
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with email is successful."""
        email = 'test_email@test.com'
        password = 'Testpass'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_user_starting_cash_balance(self):
        """Test that new user have chash balance equal 0.0"""
        user = get_user_model().objects.create_user(
            email='Test@example.com',
            password='Testpass',
        )
        self.assertEqual(user.cash_balance, 0.0)

    def test_new_user_email_normalizer(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['tEst2@example.com', 'tEst2@example.com'],
            ['TEST3@exAMple.COM', 'TEST3@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email,
                password='Testpass',
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a new user without an email raises ValuerError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email='', password='Testpass')

    def test_create_supersuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            email='Test@example.com',
            password='Test123',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_investment(self):
        """Test creating investment is successful."""
        user = get_user_model().objects.create_user(
            email='test@example.com',
            password='Testpass123',
        )
        investment = models.Investment.objects.create(
            user=user,
            title='Test title',
            asset_name='Test Name',
            type='bond',
            quantity=10.0,
            purchase_price=5.7,
            current_price=11.2,
        )

        self.assertEqual(str(investment), investment.title)

    def test_create_transaction_history(self):
        """Test create transaction history model successful."""
        user = get_user_model().objects.create_user(
            email='test@example.com',
            password='Testpass123',
            name='Test Name',
        )
        investment = models.Investment.objects.create(
            user=user,
            title='Test title',
            asset_name='Test Name',
            type='bond',
            quantity=10.0,
            purchase_price=5.7,
            current_price=11.2,
        )
        transaction_history = models.TransactionHistory.objects.create(
            investment=investment,
            user=user,
            transaction_id=investment.transaction_id,
            transaction_type='buy',
            type=investment.type,
            quantity=investment.quantity,
            purchase_price=investment.purchase_price,
            sale_price=0,
            purchase_date=timezone.now(),
        )

        self.assertEqual(str(transaction_history),
        f'{transaction_history.transaction_id} by {user.name}'
        )
