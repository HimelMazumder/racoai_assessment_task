from django.db import models

# Create your models here.

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True) # auto_now_add - on first time creation only
    updated_at = models.DateTimeField(auto_now=True) # auto_now - on every time update

    class meta:
        indexes = [
            models.Index(fields=['sku'],)
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"
