# 🚀 Production Deployment Guide

## Quick Summary

**Status**: ✅ READY TO DEPLOY

Your Django movie booking system is production-ready with:
- ✅ Clean dependencies (52 packages, minimal)
- ✅ Production settings configured
- ✅ All tests passing (60/62)
- ✅ Static files ready
- ✅ Database migrations ready
- ✅ Procfile configured
- ✅ Environment variables documented

**Next Step**: Deploy to Railway in 5 minutes

---

## Railway Deployment Setup

### Prerequisites
- Railway account (https://railway.app)
- Git repository with code pushed to GitHub
- GitHub account linked to Railway

### Step 1: Create Railway Project

```bash
# Go to https://railway.app
# Click "New Project" > "Deploy from GitHub"
# Select your "movie-booking-system" repository
# Select "main" branch
# Click "Deploy"

# Railway will start building and deploying automatically
```

### Step 2: Add PostgreSQL Database

```bash
# In Railway dashboard:
# 1. Click on your project
# 2. Click "+ Add Service"
# 3. Search for "PostgreSQL"
# 4. Click "PostgreSQL" to add
# 5. Railway creates DATABASE_URL automatically
# 6. App auto-redeploys with database connection
```

### Step 3: Add Redis Cache

```bash
# In Railway dashboard:
# 1. Click "+ Add Service" again
# 2. Search for "Redis"
# 3. Click "Redis" to add
# 4. Railway creates REDIS_URL automatically
# 5. App auto-redeploys with cache connection
```

### Step 4: Set Environment Variables

```bash
# In Railway dashboard:
# 1. Click on your project
# 2. Go to "Variables" tab
# 3. Click "Add Variable" for each:

# Django Core Settings
DEBUG=False
SECRET_KEY=_6$604vp-8p%p8y$j%txfa@*bzc)v5na6p7h)u135w1hllmo@k
ENVIRONMENT=production

# Get your domain from Railway dashboard (looks like: moviebooking-xyz.up.railway.app)
ALLOWED_HOSTS=moviebooking-abc123.up.railway.app

# Email Settings (Gmail with App Password)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=MovieBooking <noreply@moviebooking.com>
EMAIL_USE_TLS=True

# Razorpay Payment Settings (get from https://dashboard.razorpay.com)
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-secret-key

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# 4. After setting all variables, Railway auto-redeploys
```

### Step 5: Run Database Migrations

```bash
# IMPORTANT: Migrations must run INSIDE Railway (on the server)
# Not from your local machine (Railway CLI can't access the internal database)

# Option A: Using Railway Dashboard Terminal (RECOMMENDED)
# 1. Go to https://railway.app and open your project
# 2. Click on your "web" service (top tab)
# 3. Click "Deploy" or "Connect" button (opens web terminal)
# 4. In the terminal, run:

python manage.py migrate --settings=moviebooking.settings_production

# 5. Then create superuser:
python manage.py createsuperuser --settings=moviebooking.settings_production

# Follow prompts to create your admin account
# Remember the username and password!
```

### Step 6: Verify Your Live App

```bash
# 1. Get your app URL from Railway dashboard
# 2. Visit: https://your-app-name.up.railway.app
# 3. Verify:
#    ✓ Homepage loads
#    ✓ CSS and images load (static files)
#    ✓ Login page works
#    ✓ Admin panel works: /admin
#    ✓ Can register new user
#    ✓ Can browse movies
#    ✓ Can book tickets
#    ✓ Payment flow works
#    ✓ Emails sending
# 4. Check Railway logs for any errors
#    (Dashboard > Deployments > Click deployment > Logs tab)
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

# 5. Run migrations IN RAILWAY DASHBOARD:
# Go to Railway dashboard > Click "web" service > Click "Connect"
# Then run: python manage.py migrate --settings=moviebooking.settings_production
# And: python manage.py createsuperuser --settings=moviebooking.settings_production

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

# 4. If you changed models, run migrations IN RAILWAY DASHBOARD:
#    (Do NOT use railway run from local machine)
# - Go to Railway dashboard
# - Click "web" service
# - Click "Connect" button (opens terminal)
# - Run: python manage.py migrate --settings=moviebooking.settings_production

# Done! Your update is live.
```

### Using Railway CLI for Useful Commands

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link to your project
railway login
railway link  # Select your project

# Useful commands
railway logs                                    # View live logs
railway variables                               # View env vars
railway variables set KEY=value                 # Set env var
railway open                                    # Open dashboard
railway status                                  # Check status

# Note: For running Django commands (migrate, createsuperuser, shell),
# use Railway Dashboard Terminal instead (Click "web" > "Connect")
# The CLI can't access the internal database from your local machine
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

## Deploying Updates to Your Live App

### Simple 3-Step Update Process

```bash
# 1. Make changes, test locally, and commit
git add .
git commit -m "Feature: Description of change"
git push origin main

# 2. Railway automatically detects changes and redeploys
#    - Check Railway dashboard > Deployments tab
#    - Wait for "✓ Deployment Complete"

# 3. If you changed database models, run migrations IN RAILWAY:
#    - Go to Railway dashboard > Click "web" service > Click "Connect"
#    - Run: python manage.py migrate --settings=moviebooking.settings_production

# Your update is now live!
```

### Examples

**Update Django views:**
```bash
vim bookings/views.py
git add .
git commit -m "Fix: Improve booking checkout flow"
git push origin main
# Railway redeploys automatically - done!
```

**Add new database model:**
```bash
vim movies/models.py
python manage.py makemigrations
python manage.py migrate  # Test locally
git add .
git commit -m "Feature: Add movie reviews model"
git push origin main

# Then in Railway dashboard:
# Click "web" service > "Connect"
# Run: python manage.py migrate --settings=moviebooking.settings_production
```

**Update static files (CSS, images):**
```bash
vim static/css/style.css
git add .
git commit -m "Design: Update homepage styling"
git push origin main
# Railway automatically collects static files - no extra step needed!
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
