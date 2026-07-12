from django.urls import path
from .views import OrderListCreateView, OrderDetailView, CheckoutView

urlpatterns = [
    path('', OrderListCreateView.as_view(), name='order-list-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/checkout/', CheckoutView.as_view(), name='order-checkout'),
]