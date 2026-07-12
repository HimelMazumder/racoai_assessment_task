# System Architecture

## High-Level Architecture

```mermaid
graph TB
    subgraph Client Layer
        FE["Frontend (Vercel)"]
        PO["Postman / Swagger UI"]
    end

    subgraph API Gateway
        NG["ngrok Tunnel (Dev)"]
    end

    subgraph Django Backend - Docker
        DRF["Django REST Framework"]
        JWT["JWT Authentication<br/>(simplejwt)"]
        
        subgraph App Modules
            UA["users app"]
            PA["products app"]
            OA["orders app"]
            PYA["payments app"]
        end

        subgraph Business Logic
            CS["Checkout Service<br/>(atomic transactions)"]
            PS["Payment Strategies<br/>(Strategy Pattern)"]
            SS["Stock Reduction<br/>(select_for_update)"]
            DFS["Category DFS<br/>(recursive traversal)"]
        end
    end

    subgraph Data Layer - Docker
        PG["PostgreSQL 15"]
        RD["Redis 7<br/>(Category Cache)"]
    end

    subgraph External Services
        ST["Stripe API"]
        BK["bKash API"]
    end

    FE -->|HTTPS| NG
    PO -->|HTTP| DRF
    NG -->|HTTP| DRF
    DRF --> JWT
    JWT --> UA
    JWT --> PA
    JWT --> OA
    JWT --> PYA

    OA --> CS
    CS --> PS
    PS -->|initiate_payment| ST
    PS -->|initiate_payment| BK
    PYA -->|webhook callback| SS

    PA --> DFS
    DFS -->|cache read/write| RD

    UA --> PG
    PA --> PG
    OA --> PG
    PYA --> PG
    SS --> PG

    ST -->|webhook| NG
    BK -->|webhook| NG
```

## Component Responsibilities

### App Layer
| Module | Responsibility |
|---|---|
| `apps.users` | Custom User model, registration, JWT login, profile |
| `apps.products` | Product CRUD, Category model, DFS tree traversal, Redis caching |
| `apps.orders` | Order/OrderItem management, checkout initiation, total calculation |
| `apps.payments` | Payment model, Strategy pattern (Stripe/bKash), webhook handlers, stock reduction |

### Service Layer
| Service | Location | Purpose |
|---|---|---|
| `checkout.py` | `apps/orders/` | Atomic checkout: lock order → validate stock → initiate payment → create Payment record |
| `services.py` | `apps/orders/` | `update_order_total()` — recalculates order total from item subtotals with row locking |
| `services.py` | `apps/payments/` | `handle_payment_callback()` — processes webhooks, updates payment/order status, triggers stock reduction |
| `services.py` | `apps/products/` | `get_cached_category_tree()` — DFS traversal with Redis cache (12hr TTL) |
| `strategies.py` | `apps/payments/` | Strategy Pattern: `BasePaymentStrategy` → `StripePaymentStrategy` / `BkashPaymentStrategy` |

### Data Layer
| Store | Purpose |
|---|---|
| PostgreSQL | Primary relational database for all models |
| Redis | Cache layer for category tree (avoids repeated DFS queries) |

## Concurrency & Safety

- **Row-level locking:** `select_for_update()` on Order and Product rows during checkout and stock reduction
- **Deadlock prevention:** Items sorted by `product_id` before locking
- **Savepoint rollback:** Nested `transaction.atomic()` isolates stock reduction failures from payment status updates
- **Atomic transactions:** All multi-table writes wrapped in `transaction.atomic()`
