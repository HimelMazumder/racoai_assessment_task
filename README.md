# E-Commerce Ordering & Payment System

A Django REST Framework backend for managing users, products, orders, and payments with support for multiple payment providers (Stripe, bKash).

- **GitHub Repository**: [racoai_assessment_task](https://github.com/HimelMazumder/racoai_assessment_task)
- **Deployed Frontend URL**: [rocoaivercel.vercel.app](https://rocoaivercel.vercel.app/)

## Tech Stack


- **Framework:** Django 6.0 + Django REST Framework
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Auth:** JWT via `djangorestframework-simplejwt`
- **API Docs:** Swagger UI via `drf-spectacular`
- **Package Manager:** `uv`
- **Containerization:** Docker + Docker Compose

## Quick Start

### Prerequisites

- Docker & Docker Compose installed
- Git

### 1. Clone & Configure

```bash
git clone https://github.com/HimelMazumder/racoai_assessment_task.git
cd racoai_assessment_task/backend
```

Create a `.env` file in the project root:

```env
POSTGRES_DB=ecommerce_db
POSTGRES_USER=root
POSTGRES_PASSWORD=1234
DATABASE_URL=postgres://root:1234@db:5432/ecommerce_db
REDIS_URL=redis://redis:6379/1
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,web
```

### 2. Build & Run

```bash
docker compose up --build -d
```

This will:
- Start PostgreSQL, Redis, and the Django dev server
- Automatically run all database migrations

### 3. Seed the Database

```bash
docker compose exec web uv run python manage.py seed
```

This creates:
- Admin superuser (`admin` / `admin1234`)
- Hierarchical categories (Electronics → Phones → Smartphones, Appliances)
- 4 sample products with varying stock levels

### 4. Access the Application

| Service | URL |
|---|---|
| API Root | http://localhost:8000/api/ |
| Swagger Docs | http://localhost:8000/api/docs/ |
| OpenAPI Schema | http://localhost:8000/api/schema/ |
| Admin Panel | http://localhost:8000/admin/ |

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/auth/register/` | Register a new user | No |
| POST | `/api/auth/login/` | Get JWT access + refresh tokens | No |
| POST | `/api/auth/token/refresh/` | Refresh access token | No |
| GET | `/api/auth/me/` | Get current user profile | Yes |

### Products (`/api/products/`)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/products/` | List all active products | No |
| GET | `/api/products/{id}/` | Get product detail | No |
| POST | `/api/products/` | Create product | Admin |
| PUT | `/api/products/{id}/` | Update product | Admin |
| DELETE | `/api/products/{id}/` | Delete product | Admin |
| GET | `/api/products/{id}/related/` | Get related products (DFS subtree) | No |
| GET | `/api/products/categories/tree/` | Get full category tree (Redis cached) | No |

### Orders (`/api/orders/`)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/orders/` | List current user's orders | Yes |
| POST | `/api/orders/` | Create a new order | Yes |
| GET | `/api/orders/{id}/` | Get order detail (with items + payments) | Yes |
| POST | `/api/orders/{id}/checkout/` | Initiate payment for an order | Yes |

### Payments (`/api/payments/`)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/payments/webhook/stripe/` | Stripe webhook callback | No |
| POST | `/api/payments/webhook/bkash/` | bKash webhook callback | No |

## Order Flow

1. User registers and logs in → receives JWT token
2. User browses products via `GET /api/products/`
3. User creates an order via `POST /api/orders/` with product IDs and quantities
4. User initiates checkout via `POST /api/orders/{id}/checkout/` with `{"provider": "stripe"}` or `{"provider": "bkash"}`
5. Payment provider confirms/fails via webhook callback
6. Order status updates to `paid` or `cancelled`
7. Stock is reduced atomically after successful payment

## Running Tests

```bash
docker compose exec -T web uv run python manage.py test apps/payments/
```

Current test suite covers:
- Stock reduction (success + out-of-stock boundary)
- Payment webhook callback flow (order → paid, stock decremented)
- Race condition handling (stock conflict with savepoint rollback)

## Exposing via ngrok (for Webhook Testing)

To test real webhook callbacks from Stripe/bKash, expose your local server:

```bash
# Install ngrok
# https://ngrok.com/download

# Start the tunnel
ngrok http 8000
```

Then configure the ngrok HTTPS URL as your webhook endpoint in the Stripe/bKash dashboard:
- Stripe: `https://<your-ngrok-url>/api/payments/webhook/stripe/`
- bKash: `https://<your-ngrok-url>/api/payments/webhook/bkash/`

Add the ngrok host to `ALLOWED_HOSTS` in `.env`:
```env
ALLOWED_HOSTS=localhost,127.0.0.1,web,<your-ngrok-subdomain>.ngrok-free.app
```

## Project Structure

```
backend/
├── apps/
│   ├── users/          # Custom User model, JWT auth, registration
│   ├── products/       # Product CRUD, Category tree (DFS), Redis cache
│   ├── orders/         # Order management, checkout, total calculation
│   └── payments/       # Payment strategies, webhooks, stock reduction
├── core/               # Django settings, root URL config
├── docs/               # Architecture diagrams, ERD, reflections
├── docker-compose.yml
├── Dockerfile
└── manage.py
```

## Frontend Application

A minimal, premium React frontend is provided in the sibling `frontend/` directory. It is built using React + Vite and styled with a glassmorphic dark-mode CSS theme.

### Features:
- **JWT Authentication**: User login/registration with secure token storage.
- **Product & Category browsing**: DFS category tree navigation with status badge indicators.
- **Cart & Order Flow**: Live cart subtotal calculations and order submission.
- **Checkout Simulator**: Switch between Stripe/bKash, retrieve transaction IDs, and simulate successful webhook events with 1 click to update database state and inventory stock level.

### Running Frontend Locally:
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Open your browser to `http://localhost:5173`.
5. Enter your Django API URL at the top of the interface (e.g. `http://localhost:8000` or your public `ngrok` domain) to connect instantly.

---

## Documentation
- **[System Architecture](docs/system_architecture.md)**: High-level overview of backend services, APIs, data stores, caching, and client integrations.
- **[ERD Diagram](docs/erd.md)**: Relational schema map displaying tables, fields, unique constraints, and foreign key rules (PROTECT, CASCADE).
- **[Stripe Payment Flow](docs/stripe_payment_flow.md)**: Step-by-step sequence diagram outlining order checkout, webhook delivery, and concurrency/stock reduction.
- **[bKash Payment Flow](docs/bkash_payment_flow.md)**: Sequence diagram showing redirect-based merchant checkout and asynchronous callback verification.
- **[Technical Reflections](docs/architectural_reflections.md)**: Written answers to the 4 main design questions (Strategy pattern structure, DFS category tree + caching logic, thread-safe stock reduction, and webhook security).
- **[Project Report](docs/project_report.md)**: Detailed report covering implementation approach, design choices, rejected alternatives, testing coverage details, and the final project verdict.


