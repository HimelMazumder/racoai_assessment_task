from abc import ABC, abstractmethod
from apps.orders.models import Order

class BasePaymentStrategy(ABC):
    @abstractmethod
    def initiate_payment(self, order: Order, **kwargs) -> dict:
        pass

    @abstractmethod
    def verify_payment(self, payload: dict) -> dict:
        pass

class StripePaymentStrategy(BasePaymentStrategy):
    def initiate_payment(self, order: Order, **kwargs) -> dict:
        try:
            # mocking the response for development purpose
            return {
                "provider": "stripe",
                "transaction_id": f"pi_mock_{order.id}",
                "status": "pending",
                "client_secret": "pk_mock_123456789",
                "raw_response": {"id": f"pi_mock_{order.id}", "status": "requires_payment_method"}
            }
        except Exception as e:
            raise Exception(f"Stripe initialization failed: {str(e)}")

    def verify_payment(self, payload: dict) -> dict:
        event_type = payload.get("type")
        data_object = payload.get("data", {}).get("object", {})

        status = "pending"
        if event_type == "payment_intent.succeeded":
            status = "success"
        elif event_type in ["payment_intent.payment_failed", "payment_intent.cancelled"]:
            status = "failed"

        return {
            "transaction_id": data_object.get("id"),
            "status": status,
            "raw_response": payload
        }

class BkashPaymentStrategy(BasePaymentStrategy):
    def initiate_payment(self, order: Order, **kwargs) -> dict:
        try:            
            # Mocking the response for development purpose
            return {
                "provider": "bkash",
                "transaction_id": f"BKASH_MOCK_{order.id}", 
                "status": "pending",
                "bkash_url": f"https://sandbox.bkash.com/payment/checkout?paymentID=BKASH_MOCK_{order.id}",
                "raw_response": {"paymentID": f"BKASH_MOCK_{order.id}", "transactionStatus": "Initiated"}
            }
        except Exception as e:
            raise Exception(f"bKash initialization failed: {str(e)}")

    def verify_payment(self, payload: dict) -> dict:
        status_map = {
            "Completed": "success",
            "Failed": "failed",
            "Cancelled": "failed"
        }
        
        bkash_status = payload.get("transactionStatus", "Initiated")
        status = status_map.get(bkash_status, "pending")
        
        return {
            "transaction_id": payload.get("paymentID"),
            "status": status,
            "raw_response": payload
        }

class PaymentContext:
    _strategies = {
        "stripe": StripePaymentStrategy(),
        "bkash": BkashPaymentStrategy(),
    }

    @classmethod
    def get_strategy(cls, provider_name: str) -> BasePaymentStrategy:
        strategy = cls._strategies.get(provider_name.lower())
        if not strategy:
            raise ValueError(f"Unknown payment provider: {provider_name}")
        return strategy

