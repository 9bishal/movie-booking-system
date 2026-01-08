# 🚀 Railway Deployment - Quick Start Guide

## What is Railway?

Railway is a modern deployment platform similar to Heroku but with better pricing and simpler deployment. It automatically:
- Detects your Python project
- Builds a Docker container
- Installs dependencies
- Runs your app
- Handles environment variables
- Manages databases and services

## Key Differences from Heroku

| Feature | Railway | Heroku |
|---------|---------|--------|
| Build Commands | Uses Procfile or Dockerfile | Uses Procfile |
| Environment | Docker containers | Dynos |
| Pricing | $5/month free tier | Paid only (no free tier) |
| Services | Auto-linked | Manual linking required |
| Setup Time | 5-10 minutes | 10-15 minutes |

## Railway Deployment Process

### 1️⃣ Prepare Your Code

```bash
# Make sure everything is committed
git add .
git commit -m "Production-ready: Clean dependencies, fixed versions"
git push origin main
```

✅ Your repo is already prepared with:
- `requirements-production.txt` - Production dependencies
- `requirements.txt` - All dependencies
- `Procfile` - Service configurations
- `railway.json` - Railway configuration
- `Dockerfile` - Container configuration
- `moviebooking/settings_production.py` - Production settings

### 2️⃣ Connect to Railway

```bash
# Option A: Using Railway Dashboard (Easiest)
# 1. Go to https://railway.app
# 2. Sign up / Login
# 3. Click "New Project"
# 4. Click "Deploy from GitHub"
# 5. Select your repository
# 6. Select "main" branch
# 7. Click "Deploy"

# Option B: Using Railway CLI
npm install -g @railway/cli
railway login
railway link  # Follow prompts
railway up    # Deploy
```

### 3️⃣ Add Services (Databases & Cache)

Railway automatically detects services from your code. You can manually add:

**PostgreSQL (Database)**
```
In Railway Dashboard:
1. Click "Add Service" button
2. Search for "PostgreSQL"
3. Click to add
4. Railway auto-creates DATABASE_URL env variable
```

**Redis (Cache)**
```
In Railway Dashboard:
1. Click "Add Service" button
2. Search for "Redis"
3. Click to add
4. Railway auto-creates REDIS_URL env variable
```

### 4️⃣ Set Environment Variables

```bash
# In Railway Dashboard:
# 1. Click on your project
# 2. Go to "Variables" tab
# 3. Click "Add Variable" and enter:
```

**Required Variables:**
```
DEBUG=False
SECRET_KEY=_6$604vp-8p%p8y$j%txfa@*bzc)v5na6p7h)u135w1hllmo@k
ENVIRONMENT=production
```

**Get your app domain from Railway dashboard, then:**
```
ALLOWED_HOSTS=your-app-name.up.railway.app
```

**Email Configuration (Gmail):**
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=MovieBooking <noreply@moviebooking.com>
EMAIL_USE_TLS=True
```

**Razorpay (Payment Gateway):**
```
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
```

**Security (Optional but recommended):**
```
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

### 5️⃣ Monitor Deployment

```bash
# In Railway Dashboard:
# 1. Go to "Deployments" tab
# 2. Watch the logs in real-time
# 3. Wait for "✓ Build successful" message
# 4. Wait for "✓ Deployment Complete" message
# 5. Your app URL will appear (e.g., moviebooking-abc123.up.railway.app)
```

### 6️⃣ Run Initial Setup

```bash
# In Railway Dashboard:
# 1. Click on your app
# 2. Go to "Settings" tab
# 3. Scroll to "Start Command" (can override if needed)
# 4. Keep the Procfile default or use Railway CLI:

railway run python manage.py migrate --settings=moviebooking.settings_production
railway run python manage.py createsuperuser --settings=moviebooking.settings_production
```

### 7️⃣ Verify Deployment

Your app is now live! Test it:

```bash
# Visit your app URL (from Railway dashboard)
https://your-app-name.up.railway.app

# Check functionality:
✅ Homepage loads (https://your-app-name.up.railway.app)
✅ Login page works (https://your-app-name.up.railway.app/accounts/login)
✅ Can register new account
✅ Can browse movies
✅ Can book tickets
✅ Payment flow works (Razorpay integration)
✅ Admin panel works (https://your-app-name.up.railway.app/admin)
✅ Static files load (CSS, images, JavaScript)
✅ No errors in Railway logs
```

## How Railway Deployment Works

### Railway's Automatic Detection

Railway automatically detects:
1. **Python project** - From `requirements.txt`, `setup.py`, or `Pipfile`
2. **Start command** - From `Procfile` or `railway.json`
3. **Build command** - From `Dockerfile` or defaults
4. **Environment** - From `railway.json` or auto-detection

### Your Project Structure

```
movie-booking-system/
├── Procfile                          ← Railway reads this for services
├── railway.json                      ← Railway configuration (optional)
├── Dockerfile                        ← Container definition
├── requirements.txt                  ← Dependencies
├── requirements-production.txt       ← Production dependencies
├── runtime.txt                       ← Python version
├── moviebooking/
│   ├── settings.py
│   ├── settings_production.py       ← Production settings
│   ├── wsgi.py
│   └── celery.py                    ← Background tasks
└── manage.py
```

### Build Process

When you push to GitHub, Railway:

1. **Detects** Python project
2. **Pulls** your code from GitHub
3. **Builds** Docker image:
   - Base image: Python 3.12
   - Installs: dependencies from `requirements.txt`
   - Adds: your code
4. **Runs** collectstatic (automatic with whitenoise)
5. **Starts** services from Procfile:
   - `web:` service (main app)
   - `worker:` service (background jobs)
   - `beat:` service (scheduled tasks)
6. **Exposes** on URL with auto-generated domain

## Procfile Explanation

Your `Procfile` defines what services Railway will run:

```procfile
web: gunicorn moviebooking.wsgi:application --timeout 120 --workers 3
worker: celery -A moviebooking worker --loglevel=info
beat: celery -A moviebooking beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

- **web**: Main HTTP server (required)
- **worker**: Background job processor (optional)
- **beat**: Scheduled tasks (optional)

You can start with just `web:` and add others later.

## Common Issues & Solutions

### Issue: "DATABASE_URL not set"
**Solution**: In Railway dashboard, add PostgreSQL service. It auto-creates DATABASE_URL.

### Issue: "REDIS_URL not set"
**Solution**: In Railway dashboard, add Redis service. It auto-creates REDIS_URL.

### Issue: "Static files not loading"
**Solution**: 
- Whitenoise is already installed (handles static files)
- Make sure whitenoise is in MIDDLEWARE (it is)
- Redeploy or clear Railway cache

### Issue: "Email not sending"
**Solution**: 
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in Railway variables
- Check Gmail app passwords (not regular password)
- Enable "Less secure app access" if using Gmail

### Issue: "App keeps restarting"
**Solution**:
- Check logs in Railway dashboard
- Verify DATABASE_URL, REDIS_URL are set
- Check if SECRET_KEY is correct
- Ensure migrations ran successfully

## How to Update Your App

Every time you want to deploy changes:

```bash
# 1. Make changes locally
# 2. Test locally
# 3. Commit changes
git add .
git commit -m "Feature: Add X, Fix Y"
git push origin main

# 4. Railway automatically redeploys
# 5. Monitor in Railway dashboard
# 6. If you modified models, run migrations:
railway run python manage.py migrate --settings=moviebooking.settings_production
```

## Useful Railway CLI Commands

```bash
# Check status
railway status

# View logs
railway logs

# View environment variables
railway variables

# Set a variable
railway variables set KEY=value

# Run a command
railway run python manage.py shell --settings=moviebooking.settings_production

# Connect to database
railway run python manage.py dbshell --settings=moviebooking.settings_production

# Open Railway dashboard
railway open

# Stop the app
railway pause

# Start the app
railway resume
```

## Cost Breakdown

**Railway Free Tier:**
- $5/month credit
- Includes:
  - PostgreSQL service
  - Redis service
  - Web app (pay-as-you-go, ~$0.10/hour)
  - Worker & Beat services

**Pricing:**
- Free tier: $5/month
- Beyond that: Pay only for what you use
- PostgreSQL: ~$10/month for production
- Redis: Included in free tier

## Migration from Heroku (if applicable)

If you were using Heroku before:

| Heroku | Railway |
|--------|---------|
| `heroku config:set KEY=VALUE` | Railway Dashboard > Variables |
| `heroku addons:create heroku-postgresql` | Railway > Add Service > PostgreSQL |
| `heroku run migrate` | `railway run python manage.py migrate` |
| `heroku logs -t` | `railway logs` |
| `Procfile` works the same | `Procfile` works the same |

## Support & Resources

- **Railway Docs**: https://docs.railway.app
- **Django Deployment**: https://docs.djangoproject.com/en/4.2/howto/deployment/
- **Procfile Reference**: https://devcenter.heroku.com/articles/procfile
- **Railway Community**: https://discord.gg/railway

## Next Steps

1. ✅ Code is ready
2. ✅ Dependencies are clean
3. ✅ Settings are configured
4. 🔄 Push to GitHub
5. 🔄 Connect to Railway
6. 🔄 Add services (PostgreSQL, Redis)
7. 🔄 Set environment variables
8. 🔄 Deploy!
9. 🔄 Run migrations
10. 🔄 Test live app

---

**Status**: ✅ Ready for Railway Deployment
**Last Updated**: 8 January 2026
**Python Version**: 3.12
**Django Version**: 4.2.0
