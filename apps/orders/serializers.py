from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.serializers import ProductSerializer
from apps.payments.models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'provider', 'transaction_id', 'status', 'raw_response', 'created_at', 'updated_at']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'subtotal']
        read_only_fields = ['price', 'subtotal']

class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemCreateSerializer(many=True)

    def create(self, validated_data):
        from apps.products.models import Product
        from django.db import transaction
        user = self.context['request'].user

        with transaction.atomic():
            order = Order.objects.create(user=user)
            for item_data in validated_data['items']:
                product = Product.objects.get(id=item_data['product_id'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item_data['quantity'],
                    price=product.price,
                )
            from apps.orders.services import update_order_total
            update_order_total(order.id)
        return order

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True) 

    class Meta:
        model = Order
        fields = ['id', 'status', 'total_amount', 'items', 'payments', 'created_at', 'updated_at']
        read_only_fields = ['status', 'total_amount', 'created_at', 'updated_at']