from django.db import models

# Create your models here.

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    # as it is a foreign key, so index to this category field is added for optimization.
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL, # If category is deleted, set category to NULL instead of deleting the product.
        related_name='products',
        null=True,
        blank=True,
    )
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True) # auto_now_add - on first time creation only
    updated_at = models.DateTimeField(auto_now=True) # auto_now - on every time update

    # as sku is unique, it will automatically be indexed.
    # class Meta:
    #     indexes = [
    #         models.Index(fields=['sku'],)
    #     ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories', 
    )
    slug = models.SlugField(unique=True) # URL and User friendly Text Version of name. e.g. "smart-phone" instead of "Smart Phone"

    def __str__(self):
        return self.name
