from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment

User = get_user_model()

class ComprehensiveAPITestCase(APITestCase):
    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_superuser(
            username='adminuser', email='admin@example.com', password='adminpassword123'
        )
        self.regular_user = User.objects.create_user(
            username='regularuser', email='regular@example.com', password='userpassword123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', email='other@example.com', password='otherpassword123'
        )

        # Create categories for tree testing
        self.electronics = Category.objects.create(name='Electronics', slug='electronics')
        self.phones = Category.objects.create(name='Phones', slug='phones', parent=self.electronics)
        self.smartphones = Category.objects.create(name='Smartphones', slug='smartphones', parent=self.phones)
        self.appliances = Category.objects.create(name='Appliances', slug='appliances')

        # Create products
        self.product_active = Product.objects.create(
            name='iPhone 15 Pro', sku='APL-IPH15P', price=999.00, stock=10, status='active', category=self.smartphones
        )
        self.product_inactive = Product.objects.create(
            name='Old Phone', sku='APL-OLD', price=200.00, stock=5, status='inactive', category=self.smartphones
        )
        self.product_no_stock = Product.objects.create(
            name='Out of Stock Phone', sku='APL-OOS', price=500.00, stock=0, status='active', category=self.smartphones
        )

        # Obtain JWT tokens
        # Admin
        resp = self.client.post('/api/auth/login/', {'username': 'adminuser', 'password': 'adminpassword123'})
        self.admin_token = resp.data['access']
        # User
        resp = self.client.post('/api/auth/login/', {'username': 'regularuser', 'password': 'userpassword123'})
        self.user_token = resp.data['access']
        # Other User
        resp = self.client.post('/api/auth/login/', {'username': 'otheruser', 'password': 'otherpassword123'})
        self.other_token = resp.data['access']

    def set_auth_header(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def clear_auth_header(self):
        self.client.credentials()

    # --- PRODUCTS & CATEGORIES API TESTS ---

    def test_list_products_only_returns_active(self):
        """Verify product list endpoint returns only active products."""
        self.clear_auth_header()
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return active products (iPhone 15 Pro, Out of stock Phone). Inactive should be filtered out.
        skus = [item['sku'] for item in response.data]
        self.assertIn('APL-IPH15P', skus)
        self.assertIn('APL-OOS', skus)
        self.assertNotIn('APL-OLD', skus)

    def test_admin_can_create_product(self):
        """Verify admins can create products via POST."""
        self.set_auth_header(self.admin_token)
        response = self.client.post('/api/products/', {
            'name': 'New Tablet',
            'sku': 'TAB-NEW',
            'description': 'A new tablet device.',
            'price': '400.00',
            'stock': 15,
            'status': 'active',
            'category_id': self.smartphones.id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(sku='TAB-NEW').exists())

    def test_regular_user_cannot_create_product(self):
        """Verify non-admin users receive 403 Forbidden when creating a product."""
        self.set_auth_header(self.user_token)
        response = self.client.post('/api/products/', {
            'name': 'Hack Tablet',
            'sku': 'TAB-HACK',
            'description': 'Hack.',
            'price': '400.00',
            'stock': 15,
            'status': 'active'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_category_tree_endpoint(self):
        """Verify the nested category tree API retrieves correct tree structure."""
        self.clear_auth_header()
        response = self.client.get('/api/products/categories/tree/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify root category names
        root_names = [cat['name'] for cat in response.data]
        self.assertIn('Electronics', root_names)
        self.assertIn('Appliances', root_names)

        # Electronics subcategories check
        electronics_node = next(cat for cat in response.data if cat['name'] == 'Electronics')
        self.assertEqual(len(electronics_node['subcategories']), 1)
        self.assertEqual(electronics_node['subcategories'][0]['name'], 'Phones')

    # --- ORDER MANAGEMENT API TESTS ---

    def test_create_order_success(self):
        """Verify user can create an order successfully."""
        self.set_auth_header(self.user_token)
        response = self.client.post('/api/orders/', {
            'items': [
                {'product_id': self.product_active.id, 'quantity': 2}
            ]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.filter(user=self.regular_user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'pending')
        # Total amount should be 999.00 * 2 = 1998.00
        self.assertEqual(float(order.total_amount), 1998.00)

    def test_create_order_inactive_product_fails(self):
        """Verify ordering an inactive product returns HTTP 400."""
        self.set_auth_header(self.user_token)
        response = self.client.post('/api/orders/', {
            'items': [
                {'product_id': self.product_inactive.id, 'quantity': 1}
            ]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inactive", response.data['items'][0])

    def test_create_order_nonexistent_product_fails(self):
        """Verify ordering a non-existent product returns HTTP 400."""
        self.set_auth_header(self.user_token)
        response = self.client.post('/api/orders/', {
            'items': [
                {'product_id': 99999, 'quantity': 1}
            ]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_orders_isolation(self):
        """Verify users can only see their own orders."""
        # Create an order for regular_user
        order_user = Order.objects.create(user=self.regular_user, total_amount=100.00)
        
        # Create an order for other_user
        order_other = Order.objects.create(user=self.other_user, total_amount=200.00)

        # Retrieve as regular_user
        self.set_auth_header(self.user_token)
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order_ids = [order['id'] for order in response.data]
        self.assertIn(order_user.id, order_ids)
        self.assertNotIn(order_other.id, order_ids)

    # --- CHECKOUT API TESTS ---

    def test_checkout_validation_insufficient_stock(self):
        """Verify checkout fails early with HTTP 400 if product is out of stock."""
        # Create an order with out-of-stock product
        order = Order.objects.create(user=self.regular_user, total_amount=500.00)
        OrderItem.objects.create(order=order, product=self.product_no_stock, quantity=2, price=500.00, subtotal=1000.00)

        self.set_auth_header(self.user_token)
        response = self.client.post(f'/api/orders/{order.id}/checkout/', {
            'provider': 'stripe'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', response.data['error'])

    def test_checkout_ownership_isolated(self):
        """Verify a user cannot initiate checkout for another user's order."""
        # Create order for other_user
        order = Order.objects.create(user=self.other_user, total_amount=999.00)
        OrderItem.objects.create(order=order, product=self.product_active, quantity=1, price=999.00, subtotal=999.00)

        # Attempt to checkout as regular_user
        self.set_auth_header(self.user_token)
        response = self.client.post(f'/api/orders/{order.id}/checkout/', {
            'provider': 'stripe'
        }, format='json')
        # Should return 404 Not Found since queryset filters by request.user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_checkout_initiation_creates_pending_payment(self):
        """Verify successful checkout creates a Payment record and returns provider details."""
        order = Order.objects.create(user=self.regular_user, total_amount=999.00)
        OrderItem.objects.create(order=order, product=self.product_active, quantity=1, price=999.00, subtotal=999.00)

        self.set_auth_header(self.user_token)
        response = self.client.post(f'/api/orders/{order.id}/checkout/', {
            'provider': 'stripe'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['provider'], 'stripe')
        self.assertEqual(response.data['status'], 'pending')
        self.assertTrue(Payment.objects.filter(order=order, provider='stripe', status='pending').exists())

    # --- WEBHOOK API TESTS ---

    def test_stripe_webhook_callback_success(self):
        """Verify Stripe webhook successfully updates order and reduces stock."""
        # Initialize order, item and payment
        order = Order.objects.create(user=self.regular_user, total_amount=999.00)
        OrderItem.objects.create(order=order, product=self.product_active, quantity=2, price=999.00, subtotal=1998.00)
        
        transaction_id = f"pi_mock_{order.id}"
        Payment.objects.create(
            order=order,
            provider='stripe',
            transaction_id=transaction_id,
            status='pending'
        )

        initial_stock = self.product_active.stock

        # Call Webhook publicly without auth token
        self.clear_auth_header()
        response = self.client.post('/api/payments/webhook/stripe/', {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': transaction_id
                }
            }
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.product_active.refresh_from_db()

        self.assertEqual(order.status, 'paid')
        # Stock should reduce by 2
        self.assertEqual(self.product_active.stock, initial_stock - 2)

        # Payment status should be updated
        payment = Payment.objects.get(order=order)
        self.assertEqual(payment.status, 'success')

    def test_bkash_webhook_callback_success(self):
        """Verify bKash webhook successfully updates order and reduces stock."""
        order = Order.objects.create(user=self.regular_user, total_amount=999.00)
        OrderItem.objects.create(order=order, product=self.product_active, quantity=1, price=999.00, subtotal=999.00)
        
        transaction_id = f"BKASH_MOCK_{order.id}"
        Payment.objects.create(
            order=order,
            provider='bkash',
            transaction_id=transaction_id,
            status='pending'
        )

        initial_stock = self.product_active.stock

        # Call Webhook publicly without auth token
        self.clear_auth_header()
        response = self.client.post('/api/payments/webhook/bkash/', {
            'paymentID': transaction_id,
            'transactionStatus': 'Completed'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.product_active.refresh_from_db()

        self.assertEqual(order.status, 'paid')
        # Stock should reduce by 1
        self.assertEqual(self.product_active.stock, initial_stock - 1)

        payment = Payment.objects.get(order=order)
        self.assertEqual(payment.status, 'success')
