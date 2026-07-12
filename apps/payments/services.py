from django.db import transaction
from django.db.models import F
from apps.payments.strategies import PaymentContext
from apps.payments.models import Payment
from apps.orders.models import Order
from apps.products.models import Product

class OutOfStockError(Exception):
    pass

def handle_payment_callback(provider_name: str, payload: dict):
    strategy = PaymentContext.get_strategy(provider_name)
    verification_data = strategy.verify_payment(payload)

    trx_id = verification_data["transaction_id"]
    new_status = verification_data["status"]

    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(transaction_id=trx_id)
            order = Order.objects.select_for_update().get(id=payment.order_id)
            
            payment.status = new_status
            payment.raw_response = verification_data["raw_response"]
            payment.save()

            if new_status == "success" and order.status == "pending":
                order.status = "paid"
                order.save()

                try:
                    # Nested transaction (savepoint) for stock reduction
                    with transaction.atomic():
                        reduce_order_stock_safely(order)
                except OutOfStockError as e:
                    # Revert stock changes, but keep payment status as successful
                    order.status = "stock_conflict" 
                    order.save()
                
            elif new_status == "failed":
                order.status = "cancelled"
                order.save()

        except Payment.DoesNotExist:
            raise ValueError(f"Transaction ID {trx_id} not found in our logs.")

def reduce_order_stock_safely(order: Order):
    # sorting products by id ensures we don't face deadlock.    
    items = sorted(order.items.all(), key=lambda x: x.product_id)

    for item in items:
        product = Product.objects.select_for_update().get(id=item.product_id)
        # we don't need this as we are locking the rows with select_for_update()        
        # product.stock = F("stock") - item.quantity

        if product.stock >= item.quantity:
            product.stock -= item.quantity
            product.save()
        else:
            raise OutOfStockError(f"Not enough stock for {product.name}")
    