"""
Tests for models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


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