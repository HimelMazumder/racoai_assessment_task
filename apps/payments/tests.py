from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from apps.payments.services import reduce_order_stock_safely, handle_payment_callback
from apps.payments.services import OutOfStockError  

User = get_user_model()

class PaymentStockReductionTestCase(TestCase):
    def setUp(self):
        # Build base entities
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.category = Category.objects.create(name='Gadgets', slug='gadgets')
        
        self.product_a = Product.objects.create(
            name='Alpha Widget', sku='WID-A', price=100.00, stock=10, status='active', category=self.category
        )
        self.product_b = Product.objects.create(
            name='Beta Gadget', sku='GAD-B', price=50.00, stock=5, status='active', category=self.category
        )

        # Build testing order
        self.order = Order.objects.create(user=self.user, status='pending', total_amount=250.00)
        self.item_a = OrderItem.objects.create(order=self.order, product=self.product_a, quantity=2, price=100.00)
        self.item_b = OrderItem.objects.create(order=self.order, product=self.product_b, quantity=1, price=50.00)

    def test_successful_stock_reduction(self):
        """Verify stock decreases cleanly when order has sufficient volume."""
        reduce_order_stock_safely(self.order)
        
        self.product_a.refresh_from_db()
        self.product_b.refresh_from_db()
        
        self.assertEqual(self.product_a.stock, 8)
        self.assertEqual(self.product_b.stock, 4)

    def test_out_of_stock_boundary_raises_exception(self):
        """Verify that an order exceeding stock limits triggers an OutOfStockError."""
        # Force high demand quantity
        self.item_b.quantity = 10
        self.item_b.save()

        with self.assertRaises(Exception):  # Catching OutOfStockError / ValueError
            reduce_order_stock_safely(self.order)

    def test_payment_success_callback_flow(self):
        """Verify successful webhooks advance status to 'paid' and subtract stock."""
        transaction_id = f"pi_mock_{self.order.id}"
        
        # 1. Seed the pending payment record that the system expects to find
        Payment.objects.create(
            order=self.order,
            provider="stripe",
            transaction_id=transaction_id,
            status="pending"
        )
        
        # 2. Structure the payload to mirror a real Stripe webhook event
        mock_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": transaction_id
                }
            }
        }
        
        handle_payment_callback("stripe", mock_payload)
        
        self.order.refresh_from_db()
        self.product_a.refresh_from_db()
        
        self.assertEqual(self.order.status, 'paid')
        self.assertEqual(self.product_a.stock, 8)

    def test_stock_conflict_savepoint_rollback(self):
        """Verify a post-payment stock collision sets order to stock_conflict without failing payment."""
        transaction_id = f"pi_mock_{self.order.id}"
        
        # 1. Seed the pending payment record
        Payment.objects.create(
            order=self.order,
            provider="stripe",
            transaction_id=transaction_id,
            status="pending"
        )
        
        # Simulate a late-stage race condition: stock drops right before callback processes
        self.product_b.stock = 0
        self.product_b.save()

        # 2. Structure the payload correctly
        mock_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": transaction_id
                }
            }
        }
        
        handle_payment_callback("stripe", mock_payload)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'stock_conflict')
        
        payment_record = Payment.objects.get(order=self.order)
        self.assertEqual(payment_record.status, 'success')