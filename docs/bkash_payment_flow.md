# bKash Payment Flow

## Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Django as Django Backend
    participant DB as PostgreSQL
    participant bKash as bKash API

    User->>Frontend: Click "Pay with bKash"
    Frontend->>Django: POST /api/orders/{id}/checkout/<br/>{"provider": "bkash"}

    Note over Django: CheckoutView receives request

    Django->>DB: SELECT ... FOR UPDATE (lock Order row)
    DB-->>Django: Order (status=pending)

    Django->>DB: Check stock for all OrderItems
    DB-->>Django: Stock levels OK

    Django->>bKash: Create Payment<br/>(initiate_payment)
    bKash-->>Django: {paymentID: "BKASH_xxx", transactionStatus: "Initiated"}

    Django->>DB: INSERT Payment record<br/>(provider=bkash, transaction_id=BKASH_xxx, status=pending)
    DB-->>Django: Payment created

    Django-->>Frontend: 200 OK {transaction_id, bkash_url, status: "pending"}
    Frontend-->>User: Redirect to bKash checkout page

    Note over User,bKash: User completes bKash payment (PIN entry)

    bKash->>Django: POST /api/payments/webhook/bkash/<br/>{paymentID: "BKASH_xxx", transactionStatus: "Completed"}

    Note over Django: BkashWebhookView → handle_payment_callback()

    Django->>DB: SELECT Payment FOR UPDATE (lock by transaction_id)
    DB-->>Django: Payment record found

    Django->>DB: UPDATE Payment status → "success"
    Django->>DB: UPDATE Order status → "paid"

    Note over Django: Nested atomic block: reduce_order_stock_safely()

    Django->>DB: SELECT Product FOR UPDATE (sorted by product_id)
    DB-->>Django: Product rows locked

    alt Stock sufficient
        Django->>DB: UPDATE Product stock -= quantity (for each item)
        Django-->>bKash: 200 OK {status: "ok"}
    else Stock insufficient (race condition)
        Note over Django: OutOfStockError raised → savepoint rollback
        Django->>DB: UPDATE Order status → "stock_conflict"
        Django-->>bKash: 200 OK {status: "ok"}
        Note over Django: Payment stays "success", order flagged for admin review
    end
```

## bKash-Specific Notes

1. **Redirect flow:** Unlike Stripe's embedded form, bKash uses a redirect-based checkout. The `bkash_url` returned from `initiate_payment()` redirects the user to the bKash payment page.

2. **Transaction status mapping:**
   | bKash Status | Internal Status |
   |---|---|
   | `Completed` | `success` |
   | `Failed` | `failed` |
   | `Cancelled` | `failed` |
   | `Initiated` | `pending` |

3. **Same webhook handler:** Both Stripe and bKash webhooks are processed by the same `handle_payment_callback()` service function. The Strategy Pattern's `verify_payment()` method normalizes each provider's payload into a common format before processing.
