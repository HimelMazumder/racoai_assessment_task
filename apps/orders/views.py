from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from apps.orders.checkout import process_order_checkout
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product', 'payments')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save()

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product', 'payments')

class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # Inside CheckoutView:
    @extend_schema(
        request=inline_serializer(
            name='CheckoutRequest',
            fields={'provider': serializers.ChoiceField(choices=['stripe', 'bkash'])}
        )
    )
    def post(self, request, pk):
        provider = request.data.get('provider')  
        if not provider:
            return Response({'error': 'provider is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            payment_info = process_order_checkout(order.id, provider)
            return Response(payment_info, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)