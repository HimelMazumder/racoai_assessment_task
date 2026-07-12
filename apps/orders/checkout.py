from django.db import transaction
from .models import Order
from apps.payments.models import Payment
from apps.payments.strategies import PaymentContext

def process_order_checkout(order_id: int, provider_name: str) -> dict:
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order_id)

            if order.status != "pending":
                raise ValueError("This order is already processed or cancelled")

            # check stock
            for item in order.items.all():
                if item.product.stock < item.quantity:
                    raise ValueError(f"Insufficient stock for product: {item.product.name}")

            strategy = PaymentContext.get_strategy(provider_name)

            payment_info = strategy.initiate_payment(order)

            Payment.objects.create(
                order=order,
                provider=provider_name.lower(),
                transaction_id=payment_info.get("transaction_id"),
                status=payment_info.get("status"),
                raw_response=payment_info.get("raw_response")
            )

            return payment_info
    except Order.DoesNotExist:
        raise ValueError("Order not found")