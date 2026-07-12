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
# added ngrok urls also
ALLOWED_HOSTS=localhost,127.0.0.1,web,squiggle-dares-trapping.ngrok-free.dev

# Stripe Settings
STRIPE_SECRET_KEY=your-stripe-secret-key-here
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key-here
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret-here
```

### Variable Reference:

- **`DATABASE_URL`**: Relational database connection URL. If running inside Docker, target `db:5432`. If running locally, target `localhost:5432`.
- **`REDIS_URL`**: Connection string for the Redis caching server. Used by the Category Tree DFS recursive caching logic.
- **`SECRET_KEY`**: A unique, random string used by Django to provide cryptographic signing.
- **`DEBUG`**: Boolean set to `True` for development stack traces and `False` for production.
- **`ALLOWED_HOSTS`**: Whitelisted list of host/domain names that this Django site can serve.
- **`STRIPE_SECRET_KEY`**: Stripe secret API key (starts with `sk_test_`). Used to perform backend payment intents creations.
- **`STRIPE_PUBLISHABLE_KEY`**: Stripe publishable API key (starts with `pk_test_`). Used in frontend checkout elements.
- **`STRIPE_WEBHOOK_SECRET`**: Stripe webhook signing secret (starts with `whsec_`). Used to verify payload integrity on webhooks callbacks.


---

## 2. Local ngrok Setup Documentation

Payment providers (Stripe, bKash) confirm transaction completion by sending asynchronous HTTP callbacks (webhooks) to the backend. Since a local development server runs on `localhost` (private network), external servers cannot connect to it directly. 

`ngrok` solves this by establishing a secure, public HTTPS tunnel to your local server.

### Step 1: Download & Install ngrok on Ubuntu
Install the official ngrok agent repository and client using the following apt-key commands:

```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update \
  && sudo apt install ngrok
```

### Step 2: Add Authtoken Configuration
Add your account's authentication token to register the client:

```bash
ngrok config add-authtoken $YOUR_AUTHTOKEN
```

### Step 3: Establish the Tunnel to local Docker Port 8000
Start the tunnel and bind it to your static domain name, mapping it to port `8000` where the Django container is exposed:

```bash
ngrok http --url=squiggle-dares-trapping.ngrok-free.dev 8000
```

This will launch the ngrok status screen showing active forwarding to `http://localhost:8000`.


### Step 4: Configure Allowed Hosts
Django blocks traffic from unknown host headers. You must add your public ngrok subdomain to your `.env` file's `ALLOWED_HOSTS` setting:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,web,squiggle-dares-trapping.ngrok-free.dev
```

*(Note: Replace `squiggle-dares-trapping.ngrok-free.dev` with the actual tunnel URL provided by ngrok).*

### Step 5: Configure Webhooks in Dashboards
Use your public ngrok address to construct the webhook URLs, and register them inside your provider dashboards:

- **Stripe Dashboard Webhook URL:**
  `https://squiggle-dares-trapping.ngrok-free.dev/api/payments/webhook/stripe/`
- **bKash Sandbox Webhook URL:**
  `https://squiggle-dares-trapping.ngrok-free.dev/api/payments/webhook/bkash/`

All incoming transaction callbacks will now be forwarded to your local development environment.
