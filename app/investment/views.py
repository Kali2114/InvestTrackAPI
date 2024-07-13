"""
Views for transaction API.
"""
from django.utils import timezone
from django.db import transaction
from rest_framework import (
    viewsets,
    permissions,
    authentication,
    status,
)
from rest_framework.response import Response
from rest_framework.decorators import action

from core.models import Investment
from investment.utils import get_current_price
from investment.serializers import InvestmentSerializer
import logging


logger = logging.getLogger(__name__)


class InvestmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing investment."""
    serializer_class = InvestmentSerializer
    queryset = Investment.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def get_queryset(self):
        """Retrieve investments for the authenticated user."""
        investments = Investment.objects.filter(user=self.request.user).order_by('-id')
        for investment in investments:
            try:
                investment.current_price = get_current_price(investment.type, investment.asset_name)
                investment.save()
            except ValueError as e:
                logger.error(f"Error while retrieving current price for {investment.asset_name}: {e}")
                investment.current_price = investment.current_price or 0
        return investments

    def perform_create(self, serializer):
        """Create a new investment."""
        validated_data = serializer.validated_data
        current_price = validated_data.get('current_price',
                                           get_current_price(
                                               validated_data['type'],
                                               validated_data['asset_name'])
                                           )
        purchase_price = validated_data.get('purchase_price', current_price)
        serializer.save(user=self.request.user, purchase_price=purchase_price, current_price=current_price)

    @action(detail=False, methods=['post'])
    def buy(self, request):
        """Buy an investment and update the user's cash balance."""
        user = request.user
        data = request.data

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        type = serializer.validated_data['type']
        asset_name = serializer.validated_data['asset_name']
        quantity = serializer.validated_data['quantity']
        current_price = get_current_price(type, asset_name)
        total_cost = current_price * quantity

        if user.cash_balance < total_cost:
            return Response(
                {'detail': 'Insufficient funds.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            user.cash_balance -= total_cost
            user.save()
            serializer.save(user=user, purchase_price=current_price, current_price=current_price)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Delete an investment and update the user's cash balance."""
        instance = self.get_object()
        user = self.request.user
        amount_to_add = instance.current_price * instance.quantity

        with transaction.atomic():
            instance.sale_price = instance.current_price
            instance.sale_date = timezone.now()
            user.cash_balance += amount_to_add
            user.save()
            instance.save()
            self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)
