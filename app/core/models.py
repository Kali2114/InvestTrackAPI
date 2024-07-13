"""
Database models.
"""
import uuid

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from core import constants


class UserManager(BaseUserManager):
    """Manage for users."""
    def create_user(self, email, password=None, **kwargs):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('Email required.')
        user = self.model(email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create, save and return a new superuser."""
        user = self.create_user(email=email, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    cash_balance = models.FloatField(default=0.0)

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Investment(models.Model):
    """Database modl for investments."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255, blank=True)
    asset_name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=constants.INVESTMENT_TYPE_CONSTANT)
    quantity = models.FloatField()
    purchase_price = models.FloatField()
    current_price = models.FloatField()
    sale_price = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sale_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title