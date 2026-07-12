from django.urls import path
from .views import StripeWebhookView, BkashWebhookView

urlpatterns = [
    path('webhook/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('webhook/bkash/', BkashWebhookView.as_view(), name='bkash-webhook'),
]