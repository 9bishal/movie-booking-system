# 🛠️ Services & Payment Setup Guide

To run the MovieBooking system fully, you need three background services: **Redis** (for seats), **Celery Worker** (for emails), and **Celery Beat** (for cleanup).

## 1. Environment Config (`.env`)

The "Authentication failed" error happens because your Razorpay keys are missing. Create a file named `.env` in the root folder (beside `manage.py`) and add:

```env
# Razorpay Keys (Get these from Razorpay Dashboard > Settings > API Keys)
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx

# Email Config (For sending confirmation tickets)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis URL (Default is usually fine)
REDIS_URL=redis://127.0.0.1:6379/1
```

---

## 2. Running Services (Open separate terminals)

### A. Start Redis

Redis stores our seat locks.

```bash
# Mac (Homebrew)
brew services start redis
# Windows/Linux
redis-server
```

### B. Start Celery Worker

This process handles sending emails in the background.

```bash
# If using venv:
./venv/bin/celery -A moviebooking worker --loglevel=info
# Or if venv is active:
celery -A moviebooking worker --loglevel=info
```

### C. Start Celery Beat

This process runs every minute to find and release expired seat reservations.

```bash
# If using venv:
./venv/bin/celery -A moviebooking beat --loglevel=info
# Or if venv is active:
celery -A moviebooking beat --loglevel=info
```

### D. Start Django Server

```bash
# If using venv:
./venv/bin/python manage.py runserver
# Or if venv is active:
python manage.py runserver
```

---

## 3. Diagnostic Commands

Run this to check if your configuration is correct:

```bash
# If using venv:
./venv/bin/python manage.py setup_payments
# Or if venv is active:
python manage.py setup_payments
```

## 4. Troubleshooting

- **Authentication Error:** I have implemented a **Mock Mode**! If your keys contain `xxxx` (like in the example), the system will automatically bypass Razorpay's real servers and simulate a successful payment so you can test your booking flow.
- **Connection Error:** Ensure Redis is running by typing `redis-cli ping`. It should answer `PONG`.
- **Emails not sending:** Ensure you are using a "Google App Password" if using Gmail, not your regular login password.
