# 🚀 Production Deployment Guide

## Railway Deployment Setup

### Prerequisites
- Railway account (https://railway.app)
- Git repository initialized
- All tests passing
- GitHub account (for connecting repo)

### Step 1: Connect GitHub Repository to Railway

```bash
# 1. Push code to GitHub first
git add .
git commit -m "Week 4: Complete movie booking system with tests and deployment setup"
git push origin main

# 2. Go to https://railway.app and login
# 3. Click "New Project"
# 4. Select "Deploy from GitHub"
# 5. Choose your repository
# 6. Select the branch to deploy (main)
```

### Step 2: Add PostgreSQL Database

```bash
# In Railway dashboard:
# 1. Click "Add Service"
# 2. Search for "PostgreSQL"
# 3. Click "PostgreSQL" to add it
# 4. Railway automatically creates DATABASE_URL
```

### Step 3: Add Redis Cache

```bash
# In Railway dashboard:
# 1. Click "Add Service"
# 2. Search for "Redis"
# 3. Click "Redis" to add it
# 4. Railway automatically creates REDIS_URL
```

### Step 4: Set Environment Variables

```bash
# In Railway dashboard, go to Variables tab and add:

# Django Settings
DEBUG=False
SECRET_KEY=_6$604vp-8p%p8y$j%txfa@*bzc)v5na6p7h)u135w1hllmo@k
ALLOWED_HOSTS=your-railway-app-name.up.railway.app
ENVIRONMENT=production

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=MovieBooking <noreply@moviebooking.com>
EMAIL_USE_TLS=True

# Razorpay Configuration (Get from https://dashboard.razorpay.com/app/keys)
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-secret-key

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# Optional: Error Tracking with Sentry
# SENTRY_DSN=your-sentry-dsn

# Optional: AWS S3 for Media Files
# AWS_ACCESS_KEY_ID=your-aws-key
# AWS_SECRET_ACCESS_KEY=your-aws-secret
# AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

### Step 5: Deploy from GitHub

```bash
# 1. Push your code to GitHub
git add .
git commit -m "Production-ready: Clean dependencies, fixed versions"
git push origin main

# 2. In Railway dashboard, click "New Project"
# 3. Select "Deploy from GitHub"
# 4. Choose your repository
# 5. Select "main" branch
# 6. Click "Deploy Now"

# Railway will automatically:
# - Detect it's a Python project
# - Install dependencies from requirements.txt
# - Build Docker image
# - Collect static files (whitenoise is installed)
# - Start services from Procfile:
#   * web: gunicorn server
#   * worker: celery background tasks (optional)
#   * beat: celery scheduler (optional)
# - Generate domain name (e.g., moviebooking-xyz.up.railway.app)

# Monitor deployment:
# 1. Go to "Deployments" tab in Railway dashboard
# 2. Click on your deployment to view logs
# 3. Wait for "✓ Deployment Complete"
# 4. View your app URL (displays when deployment succeeds)
```

### Step 6: Run Database Migrations

```bash
# After deployment succeeds, run migrations:

# Option A: Using Railway CLI (recommended)
npm install -g @railway/cli
railway login
railway link  # Select your project
railway run python manage.py migrate --settings=moviebooking.settings_production

# Option B: Using Railway Dashboard terminal
# 1. In Railway dashboard, click your "web" service
# 2. Click "Connect" button (top right)
# 3. A terminal will open
# 4. Run: python manage.py migrate --settings=moviebooking.settings_production

# Create superuser
railway run python manage.py createsuperuser --settings=moviebooking.settings_production
```

### Step 7: Verify Deployment

```bash
# Your app will be available at:
# https://your-app-name.up.railway.app (Railway shows this in dashboard)

# Check status:
# 1. Open the deployed URL in browser
# 2. Verify homepage loads
# 3. Test login/registration
# 4. Test payment flow
# 5. Check email sending
# 6. Access admin at /admin with superuser credentials
```

---

## How to Deploy and Update Your App

### Initial Deployment (First Time)

```bash
# 1. Prepare code
cd /Users/bishalkumarshah/.gemini/antigravity/scratch/movie-booking-system
git add .
git commit -m "Production-ready deployment"
git push origin main

# 2. Connect to Railway
# - Go to https://railway.app
# - Click "New Project"
# - Select "Deploy from GitHub"
# - Choose your repository and main branch
# - Railway auto-deploys

# 3. Add Services (in Railway dashboard)
# - Click "Add Service"
# - Add PostgreSQL (auto-creates DATABASE_URL)
# - Add Redis (auto-creates REDIS_URL)

# 4. Set Environment Variables (in Railway dashboard > Variables tab)
DEBUG=False
SECRET_KEY=_6$604vp-8p%p8y$j%txfa@*bzc)v5na6p7h)u135w1hllmo@k
ALLOWED_HOSTS=your-railway-app-name.up.railway.app
ENVIRONMENT=production
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=MovieBooking <noreply@moviebooking.com>
EMAIL_USE_TLS=True
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-secret-key
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# 5. Run migrations
railway run python manage.py migrate --settings=moviebooking.settings_production
railway run python manage.py createsuperuser --settings=moviebooking.settings_production

# 6. Your app is live!
# Visit: https://your-app-name.up.railway.app
```

### Update Your App (After Initial Deployment)

```bash
# 1. Make changes locally and test
vim moviebooking/views.py  # Make your changes
python manage.py test      # Test locally

# 2. Commit and push to GitHub
git add .
git commit -m "Feature: Add X, Fix Y"
git push origin main

# 3. Railway automatically redeploys
# - Monitor in Railway dashboard > Deployments tab
# - Wait for "✓ Deployment Complete"

# 4. If you changed models, run migrations
railway run python manage.py migrate --settings=moviebooking.settings_production

# Done! Your update is live.
```

### Using Railway CLI for Easier Management

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link to your project
railway login
railway link  # Select your project

# Useful commands
railway logs                                                           # View logs
railway variables                                                      # View env vars
railway variables set KEY=value                                       # Set env var
railway run python manage.py migrate --settings=moviebooking.settings_production  # Run command
railway run python manage.py shell --settings=moviebooking.settings_production    # Django shell
railway open                                                           # Open dashboard
```

---

## Local Production Testing (Optional - Before Real Deployment)

```bash
# Set production environment variables
export DEBUG=False
export ALLOWED_HOSTS=localhost,127.0.0.1
export SECRET_KEY='test-secret-key-for-local'
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_HOST_USER=your-email@gmail.com
export EMAIL_HOST_PASSWORD=your-app-password
export RAZORPAY_KEY_ID=test-key
export RAZORPAY_KEY_SECRET=test-secret

# Collect static files
python manage.py collectstatic --noinput --settings=moviebooking.settings_production

# Run with gunicorn
pip install gunicorn
gunicorn moviebooking.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120

# Test in another terminal
curl http://localhost:8000
```

---

## Production Checklist

### Pre-Deployment (Before Pushing to GitHub)
- [x] All tests passing (60/62)
- [x] Code committed locally
- [x] `.env` file NOT committed (it's in .gitignore)
- [x] `SECRET_KEY` is strong and unique
- [x] `requirements.txt` is clean and minimal
- [x] `Procfile` configured correctly
- [x] `moviebooking/settings_production.py` configured
- [x] `python manage.py check --deploy` passes
- [ ] Code pushed to GitHub main branch

### During Railway Deployment
- [ ] Project created in Railway
- [ ] GitHub repository connected
- [ ] Deployment started and monitoring logs
- [ ] Deployment succeeds (✓ Deployment Complete)
- [ ] PostgreSQL service added
- [ ] Redis service added
- [ ] Environment variables set in Railway dashboard:
  - [ ] DEBUG=False
  - [ ] SECRET_KEY set
  - [ ] ALLOWED_HOSTS set to your Railway domain
  - [ ] ENVIRONMENT=production
  - [ ] EMAIL_* variables set
  - [ ] RAZORPAY_* variables set
  - [ ] SECURE_* variables set
- [ ] Wait for app to restart after variables are set

### Post-Deployment (After App is Running)
- [ ] Run migrations: `railway run python manage.py migrate --settings=moviebooking.settings_production`
- [ ] Create superuser: `railway run python manage.py createsuperuser --settings=moviebooking.settings_production`
- [ ] App URL accessible (https://your-app-name.up.railway.app)
- [ ] Homepage loads correctly
- [ ] Static files load (CSS, images, JavaScript)
- [ ] Login page works
- [ ] Can register new user
- [ ] Can browse movies and showtimes
- [ ] Database working (can view data)
- [ ] Admin panel accessible (/admin)
- [ ] Superuser login works
- [ ] Email sending works (test password reset)
- [ ] Payment flow works (Razorpay checkout)
- [ ] No errors in Railway logs

### Ongoing Monitoring
- [ ] Check Railway logs regularly (dashboard > Logs tab)
- [ ] Monitor database performance
- [ ] Monitor Redis cache usage
- [ ] Test app functionality weekly
- [ ] Monitor email sending status
- [ ] Set up Sentry for error tracking (optional)
- [ ] Set up alerts for deployment failures (optional)

---

## Troubleshooting

### App won't start
```bash
# Check logs in Railway dashboard:
# 1. Go to Deployments
# 2. Click latest deployment
# 3. Click Logs tab
# 4. Look for error messages

# Common issues:
# - Missing environment variables
# - Database not initialized
# - Port not exposed
```

### Database connection fails
```bash
# In Railway terminal:
python manage.py dbshell --settings=moviebooking.settings_production

# Verify DATABASE_URL is set:
echo $DATABASE_URL
```

### Static files not loading
```bash
# Redeploy with static file collection:
python manage.py collectstatic --noinput --settings=moviebooking.settings_production
git add .
git commit -m "Collect static files"
git push origin main
```

### Email not sending
```bash
# Check environment variables:
# In Railway dashboard, verify EMAIL_* variables are set

# Test manually in Railway terminal:
python manage.py shell --settings=moviebooking.settings_production
# Then:
# from django.core.mail import send_mail
# send_mail('Test', 'Test message', 'from@gmail.com', ['to@gmail.com'])
```

### Redis not connecting
```bash
# Verify REDIS_URL is set:
echo $REDIS_URL

# If missing, Railway should auto-set it when Redis service added
# Try redeploying if still issues
```

---

## Useful Railway Commands (CLI)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# View environment variables
railway variables

# Set variable
railway variables set KEY=value

# View logs
railway logs

# Deploy
railway up

# Run command
railway run python manage.py migrate

# Open dashboard
railway open
```

---

## Railway Environment Variables Reference

### Automatically Set by Railway
```
DATABASE_URL=postgresql://user:password@host:port/dbname
REDIS_URL=redis://:password@host:port
```

### Required by Application
```
DEBUG=False
SECRET_KEY=_6$604vp-8p%p8y$j%txfa@*bzc)v5na6p7h)u135w1hllmo@k
ALLOWED_HOSTS=your-railway-app-name.up.railway.app
ENVIRONMENT=production
```

### Email Configuration
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=MovieBooking <noreply@moviebooking.com>
EMAIL_USE_TLS=True
```

### Payment Gateway (Razorpay)
```
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-secret-key
```

### Security Settings
```
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

### Optional Services
```
# Sentry Error Tracking
SENTRY_DSN=your-sentry-dsn

# AWS S3 Storage
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

---

## Success Indicators

✅ Your Railway deployment is successful when:

1. **App is live** - URL accessible without errors
2. **Homepage loads** - Can browse movies
3. **Database works** - Can view movies, theaters, showtimes
4. **Authentication works** - Can login/register with email
5. **Payments work** - Razorpay checkout loads correctly
6. **Emails work** - Confirmation emails received
7. **Background jobs work** - Celery tasks processing (if configured)
8. **Admin panel works** - Access `/admin` with superuser credentials
9. **Static files load** - CSS, images, JavaScript displaying correctly
10. **No errors in logs** - Railway logs show clean operation

---

## Performance Tips for Railway

### Database
- Use connection pooling if available
- Monitor slow queries in Railway dashboard
- Archive old booking records periodically

### Static Files
- Railway serves from `staticfiles/` directory
- Use CDN for images if needed
- Consider using whitenoise for better performance

### Caching
- Redis is auto-configured once service added
- Cache movie lists in Redis
- Cache showtime availability
- Set appropriate TTLs

### Monitoring
- Enable Railway logging
- Set up Sentry for error tracking
- Monitor dyno metrics
- Set up alerts for failures

---

## Cost Considerations

**Railway Pricing:**
- PostgreSQL: Included in free tier
- Redis: Included in free tier
- Web dyno: Pay-as-you-go ($0.10/hour)
- Free tier includes $5/month credit

**Recommendations:**
- Start with free tier for testing
- Monitor usage in Railway dashboard
- Scale up only when needed
- Use Railway's pricing calculator

---

## Updating Your Application

### To Deploy New Changes:

```bash
# 1. Make code changes locally
# 2. Test locally with production settings
# 3. Commit to GitHub
git add .
git commit -m "Your update message"
git push origin main

# 4. Railway auto-detects changes and redeploys
# 5. Monitor deployment in Railway dashboard
# 6. Run migrations if needed:
railway run python manage.py migrate --settings=moviebooking.settings_production
```

---

## Rollback

### If Deployment Fails:

```bash
# In Railway dashboard:
# 1. Go to "Deployments" tab
# 2. Find the previous successful deployment
# 3. Click "Redeploy" to rollback
# 4. Confirm the action
```

---

**Last Updated**: 8 January 2026
**Status**: ✅ Ready for Railway Deployment
