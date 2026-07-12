# Technical Implementation Reflections & Verification

This document contains our responses to the key technical design questions from the assessment submission, accompanied by code verifications referencing exact files and implementation details.

---

## 1. Strategy Pattern

### Submission Response
I created a base abstract class `BasePaymentStrategy` defining two main methods: `initiate_payment` (which hits the provider's API to initialize the transaction) and `verify_payment` (which parses and normalizes the provider's webhook payload). I then wrote concrete strategy classes for Stripe and bKash to implement these methods. A central `PaymentContext` registry class exposes a `get_strategy(provider_name)` helper to resolve the correct class at runtime.

Adding a third provider (like SSLCommerz or Nagad) is simple. You just write a new subclass of `BasePaymentStrategy`, implement the API logic for initiation and verification, and add it to the `PaymentContext._strategies` dictionary. Because the checkout and webhook views only interact with the normalized methods on the base strategy, you don't have to touch any of your existing view logic.

### Code Verification
*   **Abstract Interface**: Defined in [strategies.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/payments/strategies.py#L4-L11).
*   **Concrete Implementations**:
    *   `StripePaymentStrategy` is at [strategies.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/payments/strategies.py#L13-L41).
    *   `BkashPaymentStrategy` is at [strategies.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/payments/strategies.py#L43-L71).
*   **Registry & Context**: `PaymentContext` is implemented at [strategies.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/payments/strategies.py#L73-L84).
*   **Client Calling Code**: Placed inside `CheckoutView` at [views.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/orders/views.py#L32).

---

## 2. DFS Algorithm & Caching

### Submission Response
For the category tree, I wrote a recursive helper function that builds the tree depth-first. It takes a parent category, fetches its active subcategories, and recursively calls itself on each child to build their respective subtrees before returning the full structured tree. 

Since hitting the database recursively is a heavy operation, I wrapped this DFS logic in Django's cache framework using Redis. The view first checks Redis for the cached tree structure. If it's a cache hit, it returns the JSON data instantly. If it's a cache miss, it runs the DFS query, caches the result in Redis with a 12-hour expiration, and then returns it. To prevent serving stale data, I added post-save and post-delete signals on the Category model to clear the Redis cache key whenever a category is added, modified, or removed.

### Code Verification
*   **DFS Algorithm**: Implemented in the `get_category_tree` function inside [services.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/products/services.py#L6-L19).
*   **Redis Cache Check/Write**: Managed by `get_cached_category_tree` inside [services.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/products/services.py#L21-L28).
*   **Cache Invalidation Signals**: Configured inside [signals.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/products/signals.py#L6-L12).
*   **API View Handler**: Routed through `CategoryTreeView` at [views.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/products/views.py#L23-L27).

---

## 3. Stock Reduction & Race Conditions

### Submission Response
The stock reduction runs inside a database transaction block (`transaction.atomic`). To prevent deadlocks when locking multiple items in a single order, the items are sorted by their `product_id` before querying. I then use PostgreSQL's `select_for_update()` to place a row-level lock on the product rows.

If two users try to purchase the same last item, the second user's database query is blocked at the database level until the first user's transaction commits or rolls back. Inside the lock, we check if the requested quantity is available. If the stock is sufficient, we decrement it and commit. If a race condition occurs and the stock is depleted, we raise a custom `OutOfStockError`, which triggers a database savepoint rollback. The webhook catching this error marks the order status as `stock_conflict` (retaining the payment log as successful) so an admin can flag it for manual review.

### Code Verification
*   **Atomic Transactions & Locks**: Handled inside `reduce_order_stock_safely` at [services.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/payments/services.py#L12-L28).
*   **Deadlock Prevention Sorting**: Found in [services.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/payments/services.py#L14).
*   **Savepoint Isolation and Fallbacks**: Implemented inside `handle_payment_callback` (which catch the `OutOfStockError` and sets `status='stock_conflict'`) at [services.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/payments/services.py#L51-L68).

---

## 4. Webhook Verification

### Submission Response
For the API endpoints, I used Django REST Framework's `AllowAny` permissions since payment provider servers call these routes publicly without our app's JWT tokens. To secure them, the webhook handlers are designed to extract the signature header sent by the provider (like Stripe's `Stripe-Signature` or bKash's verification headers) and verify it using the provider's official SDK library with a shared webhook signing secret.

If the signature verification succeeds, we lookup the corresponding transaction ID in our `Payment` database. We make sure the payment record exists and is currently in a `pending` status before modifying anything. This prevents attackers from spoofing payloads or trying to replay successful transactions, as any payload with an invalid signature or unrecognized transaction ID is rejected immediately.

### Code Verification
*   **Public Access Configuration**: Explicitly allowed using `permission_classes = [AllowAny]` on both `StripeWebhookView` and `BkashWebhookView` inside [views.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/payments/views.py#L11-L24).
*   **Transaction Lookup & Status Guards**: Processed securely in `handle_payment_callback` inside [services.py](file:///home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/apps/payments/services.py#L38-L47).
