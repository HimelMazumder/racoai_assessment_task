from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with initial core e-commerce data assets'

    def handle(self, *args, **kwargs):
        self.stdout.write("Initializing database seeding...")

        # 1. Create Admin Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin', 
                email='admin@example.com', 
                password='admin1234'
            )
            self.stdout.write(self.style.SUCCESS(' Successfully created superuser: admin/admin1234'))
        else:
            self.stdout.write('Superuser "admin" already exists.')

        # 2. Create Hierarchical Categories (Testing DFS logic)
        electronics, _ = Category.objects.get_or_create(name='Electronics', slug='electronics')
        phones, _ = Category.objects.get_or_create(name='Phones', slug='phones', parent=electronics)
        smartphones, _ = Category.objects.get_or_create(name='Smartphones', slug='smartphones', parent=phones)
        appliances, _ = Category.objects.get_or_create(name='Appliances', slug='appliances')

        self.stdout.write(self.style.SUCCESS(' Successfully seeded category hierarchy (DFS compatible)'))

        # 3. Create Sample Products
        products_data = [
            {
                'name': 'iPhone 15 Pro',
                'sku': 'APL-IPH15P',
                'description': 'Flagship Apple smartphone with Titanium design.',
                'price': 999.00,
                'stock': 50,
                'category': smartphones
            },
            {
                'name': 'Samsung Galaxy S24 Ultra',
                'sku': 'SAM-S24U',
                'description': 'Premium Android smartphone with AI capabilities.',
                'price': 1199.00,
                'stock': 35,
                'category': smartphones
            },
            {
                'name': 'M1 MacBook Air',
                'sku': 'APL-MBA-M1',
                'description': 'Lightweight high-performance laptop.',
                'price': 899.00,
                'stock': 12,
                'category': electronics
            },
            {
                'name': 'Smart Microwave Oven',
                'sku': 'APP-SMO-01',
                'description': 'Inverter microwave with application integration.',
                'price': 249.00,
                'stock': 0,  # Seeded out-of-stock to test boundary validation
                'category': appliances
            }
        ]

        for p_info in products_data:
            product, created = Product.objects.get_or_create(
                sku=p_info['sku'],
                defaults={
                    'name': p_info['name'],
                    'description': p_info['description'],
                    'price': p_info['price'],
                    'stock': p_info['stock'],
                    'category': p_info['category'],
                    'status': 'active'
                }
            )
            if created:
                self.stdout.write(f" Created product: {product.name}")

        self.stdout.write(self.style.SUCCESS('🎉 Database seeding complete!'))