# 🚀 Railway Setup - Step by Step Instructions

## ✅ Current Status: Project Created

Your Railway project `movie_booking_app` has been created!

**Project URL**: https://railway.com/project/cdf07706-3903-40d0-a013-2a51cf6f223c

---

## 📝 Next Steps - Add Services

### Step 1: Add PostgreSQL Database

**Option A: Using Railway CLI**
```bash
railway service add PostgreSQL
```

**Option B: Using Railway Dashboard**
1. Go to https://railway.com/project/cdf07706-3903-40d0-a013-2a51cf6f223c
2. Click "+ Add Service"
3. Click "PostgreSQL"
4. Wait for service to be created

### Step 2: Add Redis Cache

**Option A: Using Railway CLI**
```bash
railway service add Redis
```

**Option B: Using Railway Dashboard**
1. Go to your project dashboard
2. Click "+ Add Service"
3. Click "Redis"
4. Wait for service to be created

---

## �� Connecting Services

After creating PostgreSQL and Redis, Railway automatically:
1. Creates connection strings (DATABASE_URL, REDIS_URL)
2. Provides environment variables
3. Configures networking between services

---

## 📤 Deploy Your Application

### Option 1: Deploy from Git

```bash
# Ensure all changes are committed
git add .
git commit -m "🚀 Prepare for Railway deployment"
git push origin main

# Then in Railway Dashboard:
# 1. Go to GitHub Integration
# 2. Connect your repository
# 3. Select movie-booking-system repo
# 4. Enable auto-deploy
```

### Option 2: Deploy Using Railway CLI

```bash
# Deploy current code
railway up
```

---

## ⚙️ Configure Environment Variables

After deployment, set environment variables in Railway Dashboard:

```
DEBUG=False
ALLOWED_HOSTS=your-domain.railway.app

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Razorpay
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret

# Site
SITE_URL=https://your-domain.railway.app
```

---

## 🗄️ Run Migrations

### Option 1: Using Railway CLI

```bash
railway shell

# Inside the shell:
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
exit
```

### Option 2: Using Railway Dashboard

1. Go to your Web service
2. Click "Shell" tab
3. Run commands:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

---

## ✅ Verify Deployment

### Check Application

```bash
# View logs
railway logs

# Check if running
curl https://your-domain.railway.app/admin/
```

### Access Django Admin

```
https://your-domain.railway.app/admin/
Username: (created via createsuperuser)
Password: (created via createsuperuser)
```

---

## 📊 Services Overview

Your deployment will have:

1. **Web Service** (Django Application)
   - Runs on port 8000
   - Exposed as public URL
   - Auto-scales based on demand

2. **PostgreSQL Service**
   - 1GB storage (free tier)
   - Automatic backups
   - High availability

3. **Redis Service**
   - In-memory data store
   - Used for caching and Celery
   - Automatic persistence

---

## 🎯 Optional: Add Celery Services

For background task processing, add:

### Celery Worker Service

```bash
# In Railway Dashboard:
# 1. Click "+ Add Service"
# 2. Click "Create New"
# 3. Name: celery-worker
# 4. Start Command: celery -A moviebooking worker -l info
# 5. Click "Deploy"
```

### Celery Beat Service

```bash
# In Railway Dashboard:
# 1. Click "+ Add Service"
# 2. Click "Create New"
# 3. Name: celery-beat
# 4. Start Command: celery -A moviebooking beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
# 5. Click "Deploy"
```

---

## 🔒 Security Configuration

### Set Secure Secret Key

```bash
# Generate a new secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Copy the output and set in Railway:
railway variables set SECRET_KEY <paste_output_here>
```

### Configure HTTPS

Railway automatically provides HTTPS for all applications. Custom domains get SSL certificates.

---

## 📈 Monitoring

Railway provides free monitoring:

1. **Logs** - Real-time application logs
2. **Metrics** - CPU, Memory, Network graphs
3. **Deployments** - View deployment history
4. **Health Checks** - Service status

Access from your project dashboard.

---

## 🚀 Commands Reference

```bash
# List all services
railway services

# View environment variables
railway variables

# Set variable
railway variables set KEY value

# Deploy code
railway up

# Open shell
railway shell

# View logs
railway logs

# View project info
railway status

# Link to existing service
railway link
```

---

## 📞 Troubleshooting

### Application won't start
```bash
# Check logs
railway logs

# Check environment variables are set
railway variables
```

### Database connection failed
```bash
# Check DATABASE_URL is set
railway variables | grep DATABASE

# Verify PostgreSQL service exists
railway services
```

### Static files not loading
```bash
# Recollect static files
railway shell
python manage.py collectstatic --noinput --clear
```

---

## 💡 Tips

1. **Use Railway Dashboard** for most tasks (easier)
2. **Monitor logs regularly** for issues
3. **Set up monitoring alerts** for production
4. **Keep database backups** enabled
5. **Test migrations locally** before deploying
6. **Use environment-specific settings** for dev/prod

---

## 📝 Files Created

For Railway deployment:
- ✅ `Dockerfile` - Container configuration
- ✅ `railway.json` - Railway-specific settings
- ✅ `Procfile` - Service definitions
- ✅ Updated `requirements.txt` - With dj-database-url
- ✅ Updated `settings.py` - PostgreSQL support

---

## 🎉 You're Ready!

Your application is configured and ready to deploy to Railway.

**Next Action**: Go to https://railway.com/project/cdf07706-3903-40d0-a013-2a51cf6f223c and add PostgreSQL and Redis services!

---

**Status**: ✅ Ready for Railway Deployment  
**Date**: January 16, 2026  
**Project**: movie_booking_app
