"""
Serializers for the investment API.
"""
from rest_framework import serializers

from core.models import Investment


class InvestmentSerializer(serializers.ModelSerializer):
    """Serializer for the investment object."""

    class Meta:
        model = Investment
        fields = [
            'id',
            'transaction_id',
            'user',
            'title',
            'asset_name',
            'type',
            'quantity',
            'purchase_price',
            'current_price',
            'created_at',
            'sale_date',
        ]
        read_only_fields = [
            'id',
            'transaction_id',
            'user',
            'current_price',
            'created_at',
            'sale_date',
        ]
        extra_kwargs = {
            'purchase_price': {'required': False}
        }

    def validate_quantity(self, value):
        """Validate that quantity is a positive number."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be a positive value.")
        return value

    def validate_current_price(self, value):
        """Validate that current price is a positive number."""
        if value <= 0:
            raise serializers.ValidationError("Current price must be a positive value.")
        return value

    def update(self, instance, validated_data):
        """Update and save investment."""
        validated_data.pop('type', None)
        validated_data.pop('purchase_price', None)
        validated_data.pop('asset_name', None)
        validated_data.pop('current_price', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def create(self, validated_data):
        """Create and return a new investment."""
        return Investment.objects.create(**validated_data)
