from django.db import transaction
from django.db.models import Sum
from .models import Order

def update_order_total(order_id):
    # all the database operation inside this function will either all succeed or all fail. i.e., atomic operation. No data inconsistency.
    with transaction.atomic():
        # select_for_update() locks the order row until the end of the transaction.
        order = Order.objects.select_for_update().get(id=order_id)

        total = order.items.aggregate(Sum("subtotal"))["subtotal__sum"] or 0.00

        order.total_amount = total
        order.save()

        return order.total_amount
        
