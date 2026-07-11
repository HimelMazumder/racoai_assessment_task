from django.db import models
from apps.orders.models import Order

# Create your models here.

class Payment(models.Model):
    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('bkash', 'Bkash'),
    ]

    STATUS_CHOICE = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    transaction_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICE, default='pending')
    raw_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.provider.upper()} Payment {self.transaction_id} - {self.status}"

    
    