from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from apps.payments.services import handle_payment_callback

class StripeWebhookView(APIView):
    permission_classes = [AllowAny]  
    authentication_classes = []

    def post(self, request):
        payload = request.data
        
        try:
            handle_payment_callback("stripe", payload)
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class BkashWebhookView(APIView):
    permission_classes = [AllowAny]  
    authentication_classes = []

    def post(self, request):
        payload = request.data
        try:
            handle_payment_callback("bkash", payload)
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)