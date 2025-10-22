from _decimal import InvalidOperation
from rest_framework import serializers
from .models import Order
from decimal import Decimal

class OrderSerializer(serializers.ModelSerializer):
    items = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = Order
        fields = ['items', 'payment_amount']
        extra_kwargs = {
            'payment_amount': {'required': True, 'min_value': Decimal('0.01')},
        }

    def validate_items(self, value):
        if not value or not all(isinstance(item, str) for item in value):
            raise serializers.ValidationError("items must be a non-empty list of strings")
        return value

    def validate_payment_amount(self, value):
        try:
            decimal_value = Decimal(str(value))
            if decimal_value <= Decimal('0.0'):
                raise serializers.ValidationError("payment_amount must be a positive number")
            return decimal_value
        except (ValueError, TypeError, InvalidOperation):
            raise serializers.ValidationError("payment_amount must be a valid positive number")

    def create(self, validated_data):
        return Order.objects.create(**validated_data)