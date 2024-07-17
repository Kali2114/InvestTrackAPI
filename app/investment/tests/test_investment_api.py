"""
Test for the investment API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Investment, TransactionHistory

from investment.serializers import (
    InvestmentSerializer,
    TransactionHistorySerializer,
)
from investment.utils import get_current_price


INVESTMENT_URL = reverse('investment:investment-list')
INVESTMENT_BUY = reverse('investment:investment-buy')
TRANSACTION_HISTORY = reverse('investment:transaction-history-list')


def investment_detail_url(investment_id):
    """Create and return investment detail url."""
    return reverse('investment:investment-detail', args=[investment_id])


def create_investment(user, **kwargs):
    """Create and return a sample investment."""
    defaults = {
        'title': 'Test title',
        'asset_name': 'bitcoin',
        'type': 'cc',
        'quantity': 10.2,
    }
    defaults.update(**kwargs)

    defaults['current_price'] = get_current_price(defaults['type'], defaults['asset_name'])
    defaults['purchase_price'] = defaults['current_price']

    investment = Investment.objects.create(user=user, **defaults)
    return investment


def create_transaction_history(user, investment, **kwargs):
    """Create and return a sample transaction history."""
    defaults = {
        'transaction_id': investment.transaction_id,
        'transaction_type': 'buy',
        'type': investment.type,
        'quantity': investment.quantity,
        'purchase_price': investment.purchase_price,
        'sale_price': investment.current_price,
        'purchase_date': investment.created_at,
        'sale_date': timezone.now()
    }
    defaults.update(**kwargs)

    return TransactionHistory.objects.create(user=user, investment=investment, **defaults)


def create_user(**kwargs):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**kwargs)


class PublicInvestmentApiTests(TestCase):
    """Test the public features of the investment API."""

    def setUp(self):
        self.client = APIClient()

    def test_authorisation_required(self):
        """Test auth is required to call API."""
        res = self.client.get(INVESTMENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateInvestmentApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            cash_balance=1000000,
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_investments(self):
        """Test retrieving a list of investments."""
        create_investment(user=self.user)
        create_investment(user=self.user, title='Another title')
        res = self.client.get(INVESTMENT_URL)

        investments = Investment.objects.all().order_by('-id')
        serializer = InvestmentSerializer(investments, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_investment_limited_to_user(self):
        """Test retrieving investments for user."""
        another_user = create_user(
            email='another@example.com',
            password='testpass123',
            name='Another User',
        )
        create_investment(user=self.user)
        create_investment(user=self.user)
        create_investment(user=another_user)
        res = self.client.get(INVESTMENT_URL)

        investments = Investment.objects.filter(user=self.user).order_by('-id')
        serializer = InvestmentSerializer(investments, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, serializer.data)


    @patch('investment.utils.TimeSeries')
    def test_buy_investment_successful_stock(self, MockTimeSeries):
        """Test buying a stock investment successfully deducts from cash balance."""
        mock_instance = MockTimeSeries.return_value
        mock_instance.get_intraday.return_value = ({
            "Meta Data": {
                "1. Information": "Intraday (5min) open, high, low, close prices and volume",
                "2. Symbol": "AAPL",
                "3. Last Refreshed": "2024-07-11 19:55:00",
                "4. Interval": "5min",
                "5. Output Size": "Compact",
                "6. Time Zone": "US/Eastern"
            },
            "Time Series (5min)": {
                "2024-07-11 19:55:00": {
                    "1. open": "228.3400",
                    "2. high": "228.5000",
                    "3. low": "227.8200",
                    "4. close": "228.2880",
                    "5. volume": "16275"
                }
            }
        }, None)

        start_balance = self.user.cash_balance
        payload = {
            'title': 'Test Stock Purchase',
            'asset_name': 'AAPL',
            'type': 'stock',
            'quantity': 1,
        }
        res = self.client.post(INVESTMENT_BUY, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        investment = Investment.objects.get(id=res.data['id'])
        self.user.refresh_from_db()
        expected_balance = start_balance - investment.current_price
        self.assertEqual(self.user.cash_balance, expected_balance)
        for k, v in payload.items():
            self.assertEqual(getattr(investment, k), v)

    def test_buy_investment_successful_cc(self):
        """Test buying a crypto investment successfully deducts from cash balance."""
        start_balance = self.user.cash_balance
        payload = {
            'title': 'Test title',
            'asset_name': 'bitcoin',
            'type': 'cc',
            'quantity': 1,
        }
        res = self.client.post(INVESTMENT_BUY, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        investment = Investment.objects.get(id=res.data['id'])
        self.user.refresh_from_db()
        expected_balance = start_balance - investment.current_price
        self.assertEqual(self.user.cash_balance, expected_balance)
        for k, v in payload.items():
            self.assertEqual(getattr(investment, k), v)

    @patch('investment.utils.get_current_price')
    def test_create_investment_negative_quantity_error(self, mock_get_current_price):
        """Test creating a new investment with negative quantity raises error."""
        mock_get_current_price.return_value = 20.5
        payload = {
            'title': 'Test title',
            'asset_name': 'Test name',
            'type': 'cc',
            'quantity': -7.2,
        }
        res = self.client.post(INVESTMENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', res.data)
        self.assertEqual(res.data['quantity'][0], 'Quantity must be a positive value.')
        exists = Investment.objects.filter(user=self.user).exists()
        self.assertFalse(exists)

    def test_created_investment_get_price(self):
        """Test that new investment get current and purchase price,"""
        investment = create_investment(user=self.user)
        url = investment_detail_url(investment.id)
        res = self.client.get(url)

        self.assertTrue(res.data['current_price'])
        self.assertTrue(res.data['purchase_price'])

    def test_update_investment_successful(self):
        """Test updating an investment is successful."""
        investment = create_investment(user=self.user)
        payload = {
            'title': 'New title',
            'quantity': 12.0,
        }
        url = investment_detail_url(investment.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        investment.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(investment, k), v)

    def test_update_investment_other_user(self):
        """Test that update another user's investment fails."""
        another_user = create_user(
            email='another@example.com',
            password='testpass123',
            name='Another User',
        )
        investment = create_investment(user=another_user)
        payload = {'title': 'New Title'}
        url = investment_detail_url(investment.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_investment_invalid(self):
        """Test that an investment with invalid data fails."""
        investment = create_investment(user=self.user)
        payload = {'current_price': -12.2}
        url = investment_detail_url(investment.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        investment.refresh_from_db()
        self.assertNotEqual(investment.current_price, payload['current_price'])

    @patch('investment.utils.get_current_price')
    def test_full_update_fails(self, mock_get_current_price):
        """Test that full update fails."""
        mock_get_current_price.return_value = 20.5
        investment = create_investment(user=self.user)
        payload = {
            'title': 'update',
            'asset_name': 'update',
            'type': 'bond',
            'quantity': 12.1,
            'purchase_price': 13.1,
            'current_price': 9.21,
        }
        url = investment_detail_url(investment.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        investment.refresh_from_db()
        data = ['asset_name', 'type', 'purchase_price', 'current_price']
        for k, v in payload.items():
            if k in data:
                self.assertNotEqual(getattr(investment, k), v)
            else:
                self.assertEqual(getattr(investment, k), v)

    def test_delete_investment_successful(self):
        """Test deleting an investment is successful and updates cash balance."""
        test_balance = self.user.cash_balance
        investment = create_investment(user=self.user)
        all_costs = investment.current_price * investment.quantity
        expected_cash_balance = test_balance + all_costs
        self.user.sale_price = all_costs
        url = investment_detail_url(investment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        exist = Investment.objects.filter(id=investment.id).exists()
        self.assertFalse(exist)
        self.user.refresh_from_db()
        self.assertEqual(self.user.cash_balance, expected_cash_balance)
        self.assertEqual(self.user.sale_price, all_costs)

    def test_retrieve_transactions_history(self):
        """Test retrieving a list of transactions history."""
        investment = create_investment(user=self.user)
        investment2 = create_investment(user=self.user)
        create_transaction_history(user=self.user, investment=investment)
        create_transaction_history(user=self.user, investment=investment2)
        res = self.client.get(TRANSACTION_HISTORY)

        transactions = TransactionHistory.objects.all().order_by('-id')
        serializer = TransactionHistorySerializer(transactions, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_transactions_history_limited_to_user(self):
        """Test retrieving transactions history for user."""
        user2 = create_user(
            email='Exampl2@test.com',
            password='Testpass123',
            name='testuser2',
        )
        investment1 = create_investment(user=self.user)
        investment2 = create_investment(user=self.user)
        another_investment = create_investment(user=user2)
        create_transaction_history(user=self.user, investment=investment1)
        create_transaction_history(user=self.user, investment=investment2)
        create_transaction_history(user=user2, investment=another_investment)
        res = self.client.get(TRANSACTION_HISTORY)

        transactions = TransactionHistory.objects.filter(user=self.user).order_by('-id')
        serializer = TransactionHistorySerializer(transactions, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, serializer.data)

    def test_create_transaction_history_while_selling_investment(self):
        """Test creating a transaction history entry while selling an investment."""
        investment = create_investment(user=self.user)
        transaction_id = investment.transaction_id
        url = investment_detail_url(investment.id)
        res = self.client.delete(url)

        transaction_exists = TransactionHistory.objects.filter(
            user=self.user,
            transaction_id=transaction_id
        ).exists()
        transaction_history = TransactionHistory.objects.filter(
            user=self.user,
            transaction_id=transaction_id
        ).first()

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(investment.transaction_id, transaction_history.transaction_id)
        self.assertTrue(transaction_exists)