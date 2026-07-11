from abc import ABC, abstractmethod

class PaymentStrategy(ABC):
    @abstractmethod
    def initiate_payment(self, order):
        pass

    @abstractmethod
    def verify_payment(self, request_data):
        pass

class StripePaymentStrategy(PaymentStrategy):
    def initiate_payment(self, order):
        pass

    def verify_payment(self, request_data):
        pass

class BkashPaymentStrategy(PaymentStrategy):
    def initiate_payment(self, order):
        pass

    def verify_payment(self, request_data):
        pass

