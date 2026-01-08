# Railway Deployment - Environment Variables Quick Copy

Copy these exactly into Railway Variables tab:

```
DEBUG=False
SECRET_KEY=_6$604vp-8p%p8y$j%txfa@*bzc)v5na6p7h)u135w1hllmo@k
ALLOWED_HOSTS=your-railway-app-name.up.railway.app
ENVIRONMENT=production
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=MovieBooking <noreply@moviebooking.com>
EMAIL_USE_TLS=True
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-secret-key
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

## What to Replace

1. **ALLOWED_HOSTS**: Change `your-railway-app-name` to your actual Railway app name
   - Example: `moviebooking-app.up.railway.app`

2. **EMAIL_HOST_USER**: Your Gmail address
   - Example: `yourname@gmail.com`

3. **EMAIL_HOST_PASSWORD**: Gmail App Password (NOT your regular password)
   - Generate at: https://myaccount.google.com/apppasswords

4. **RAZORPAY_KEY_ID**: From Razorpay Dashboard
   - https://dashboard.razorpay.com/app/keys

5. **RAZORPAY_KEY_SECRET**: From Razorpay Dashboard
   - https://dashboard.razorpay.com/app/keys

## PostgreSQL & Redis
Railway auto-sets these, you DON'T need to add:
- `DATABASE_URL` (auto-set by PostgreSQL service)
- `REDIS_URL` (auto-set by Redis service)

## All Set!
Once you set these variables in Railway:
1. Click Deploy
2. Go to Deployments → Connect → Terminal
3. Run: `python manage.py migrate --settings=moviebooking.settings_production`
4. Run: `python manage.py createsuperuser --settings=moviebooking.settings_production`
5. Open your Railway app URL
6. Login and test!
