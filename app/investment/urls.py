"""
Urls mappings for investment API.
"""
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from investment.views import InvestmentViewSet, TransactionHistoryView

router = DefaultRouter()
router.register('investments', InvestmentViewSet, basename='investment')
router.register('transactions', TransactionHistoryView, basename='transaction-history')

app_name = 'investment'

urlpatterns = [
    path('', include(router.urls)),
    path('investments/buy/', InvestmentViewSet.as_view({'post': 'buy'}), name='investment-buy'),
]