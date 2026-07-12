# Environment Configuration & Local ngrok Setup Guide

This guide describes how to configure the environment variables and expose the local development server to the internet using `ngrok` to receive payment webhooks from Stripe and bKash.

---

## 1. Environment Configuration Guide

The project uses `django-environ` to load configurations from a `.env` file located in the project root directory.

### Steps to Configure:

1. Create a file named `.env` in the root directory: `/home/dev-108/Desktop/dev-108/temp/racoai_assessment_task/backend/.env`
2. Populate the file with the following variables:

```env
# Database Settings (PostgreSQL)
POSTGRES_DB=ecommerce_db
POSTGRES_USER=root
POSTGRES_PASSWORD=1234
DATABASE_URL=postgres://root:1234@db:5432/ecommerce_db

# Cache Settings (Redis)
REDIS_URL=redis://redis:6379/1

# Django Core Settings
SECRET_KEY=your-super-secure-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,web
```

### Variable Reference:

- **`DATABASE_URL`**: Relational database connection URL. If running inside Docker, target `db:5432`. If running locally, target `localhost:5432`.
- **`REDIS_URL`**: Connection string for the Redis caching server. Used by the Category Tree DFS recursive caching logic.
- **`SECRET_KEY`**: A unique, random string used by Django to provide cryptographic signing.
- **`DEBUG`**: Boolean set to `True` for development stack traces and `False` for production.
- **`ALLOWED_HOSTS`**: Whitelisted list of host/domain names that this Django site can serve.

---

## 2. Local ngrok Setup Documentation

Payment providers (Stripe, bKash) confirm transaction completion by sending asynchronous HTTP callbacks (webhooks) to the backend. Since a local development server runs on `localhost` (private network), external servers cannot connect to it directly. 

`ngrok` solves this by establishing a secure, public HTTPS tunnel to your local server.

### Step 1: Download & Install ngrok
Download the ngrok client suitable for your Operating System:
- **Linux / macOS / Windows:** Download from [ngrok.com/download](https://ngrok.com/download)
- Add the executable to your system path.

### Step 2: Establish the Tunnel
Run the following command in a new terminal window to expose your local port `8000`:

```bash
ngrok http 8000
```

This will launch a status screen displaying a public HTTPS URL (e.g., `https://a1b2-34-56-78.ngrok-free.app`).

### Step 3: Configure Allowed Hosts
Django blocks traffic from unknown host headers. You must add your public ngrok subdomain to your `.env` file's `ALLOWED_HOSTS` setting:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,web,a1b2-34-56-78.ngrok-free.app
```

*(Note: Replace `a1b2-34-56-78.ngrok-free.app` with the actual tunnel URL provided by ngrok).*

### Step 4: Configure Webhooks in Dashboards
Use your public ngrok address to construct the webhook URLs, and register them inside your provider dashboards:

- **Stripe Dashboard Webhook URL:**
  `https://a1b2-34-56-78.ngrok-free.app/api/payments/webhook/stripe/`
- **bKash Sandbox Webhook URL:**
  `https://a1b2-34-56-78.ngrok-free.app/api/payments/webhook/bkash/`

All incoming transaction callbacks will now be forwarded to your local development environment.
