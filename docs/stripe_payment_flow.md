# Stripe Payment Flow

## Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Django as Django Backend
    participant DB as PostgreSQL
    participant Stripe as Stripe API

    User->>Frontend: Click "Pay with Stripe"
    Frontend->>Django: POST /api/orders/{id}/checkout/<br/>{"provider": "stripe"}
    
    Note over Django: CheckoutView receives request

    Django->>DB: SELECT ... FOR UPDATE (lock Order row)
    DB-->>Django: Order (status=pending)
    
    Django->>DB: Check stock for all OrderItems
    DB-->>Django: Stock levels OK

    Django->>Stripe: Create Payment Intent<br/>(initiate_payment)
    Stripe-->>Django: PaymentIntent {id: "pi_xxx", status: "requires_payment_method"}

    Django->>DB: INSERT Payment record<br/>(provider=stripe, transaction_id=pi_xxx, status=pending)
    DB-->>Django: Payment created

    Django-->>Frontend: 200 OK {transaction_id, client_secret, status: "pending"}
    Frontend-->>User: Show Stripe payment form

    Note over User,Stripe: User completes card payment on Stripe

    Stripe->>Django: POST /api/payments/webhook/stripe/<br/>{type: "payment_intent.succeeded", data: {object: {id: "pi_xxx"}}}

    Note over Django: StripeWebhookView → handle_payment_callback()

    Django->>DB: SELECT Payment FOR UPDATE (lock by transaction_id)
    DB-->>Django: Payment record found

    Django->>DB: UPDATE Payment status → "success"
    Django->>DB: UPDATE Order status → "paid"

    Note over Django: Nested atomic block: reduce_order_stock_safely()

    Django->>DB: SELECT Product FOR UPDATE (sorted by product_id)
    DB-->>Django: Product rows locked
    
    alt Stock sufficient
        Django->>DB: UPDATE Product stock -= quantity (for each item)
        Django-->>Stripe: 200 OK {status: "ok"}
    else Stock insufficient (race condition)
        Note over Django: OutOfStockError raised → savepoint rollback
        Django->>DB: UPDATE Order status → "stock_conflict"
        Django-->>Stripe: 200 OK {status: "ok"}
        Note over Django: Payment stays "success", order flagged for admin review
    end
```

## Key Design Decisions

1. **Pre-checkout stock validation:** Before calling Stripe, we check stock levels to avoid unnecessary payment intents for out-of-stock products.

2. **Post-payment stock reduction:** Stock is only deducted *after* payment confirmation via webhook, not during checkout initiation. This prevents stock being "reserved" for abandoned payments.

3. **Savepoint isolation:** If stock runs out between checkout and webhook (race condition), the payment record stays `success` but the order is marked `stock_conflict`. This ensures billing accuracy while flagging fulfillment issues.

4. **Row-level locking:** `select_for_update()` on both Order and Product rows prevents concurrent modifications during critical sections.
