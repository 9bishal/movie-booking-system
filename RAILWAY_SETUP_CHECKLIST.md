# Railway Deployment Checklist

## Before You Deploy - Things to Change/Set

### 1. Generate Strong SECRET_KEY
```bash
# Generate a new SECRET_KEY (don't use the development one)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Copy the output - you'll need it for Railway
```

### 2. Prepare GitHub Push
```bash
git add .
git commit -m "Week 4: Complete movie booking system with tests and deployment setup"
git push origin main
```

### 3. Railway Environment Variables to Set

In Railway dashboard Variables tab, set EXACTLY these:

```
DEBUG=False
SECRET_KEY=[paste the generated key from step 1]
ALLOWED_HOSTS=your-app-name.up.railway.app
ENVIRONMENT=production

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-secret-key
```

### 4. Gmail App Password (if using Gmail for emails)
- Go to https://myaccount.google.com/apppasswords
- Generate an app password for "Mail"
- Use this as EMAIL_HOST_PASSWORD (not your regular Gmail password)

### 5. Razorpay Keys
- Get from: https://dashboard.razorpay.com/app/keys
- Copy Key ID and Secret
- Use Test keys first for testing, then Production keys

### 6. Check Production Settings
✅ DEBUG = False (already set in settings_production.py)
✅ ALLOWED_HOSTS configured (already in code)
✅ SECURE_SSL_REDIRECT = True (already set)
✅ SESSION_COOKIE_SECURE = True (already set)
✅ CSRF_COOKIE_SECURE = True (already set)
✅ Database: PostgreSQL (Railway auto-sets DATABASE_URL)
✅ Cache: Redis (Railway auto-sets REDIS_URL)
✅ Static files: Whitenoise (already in requirements-production.txt)

### 7. What's Already Done
✅ All tests passing (53/53)
✅ Dockerfile created and fixed
✅ Procfile with web/worker/beat processes
✅ requirements-production.txt with all dependencies
✅ settings_production.py with security settings
✅ Logging configured
✅ Cache (Redis) configured
✅ Celery configured
✅ Email backend ready
✅ Static files collection ready

### 8. Railway Setup Steps
1. Create Railway account at https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Connect your GitHub repo
5. Add PostgreSQL service
6. Add Redis service
7. Set environment variables (from step 3)
8. Configure build command: `pip install -r requirements-production.txt && python manage.py collectstatic --noinput --settings=moviebooking.settings_production`
9. Configure start command: `gunicorn moviebooking.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120`
10. Deploy!

### 9. After Deployment
```bash
# Connect to Railway terminal and run:
python manage.py migrate --settings=moviebooking.settings_production
python manage.py createsuperuser --settings=moviebooking.settings_production
```

### 10. Test the Live App
- Open https://your-app-name.up.railway.app
- Test login/registration with email
- Test booking flow
- Test Razorpay payment
- Check that emails are being sent
- Access admin panel with superuser

---

**That's it! Everything else is already configured. Just set the env variables and deploy!**
