# 🚀 Railway Deployment Guide for Movie Booking System

## ✅ Status: Ready to Deploy

This guide will help you deploy the Django Movie Booking System to Railway with PostgreSQL, Redis, and all necessary services.

---

## 📋 Prerequisites

- ✅ Railway CLI installed
- ✅ Railway account (logged in with `railway login --browserless`)
- ✅ Git repository ready
- ✅ Project initialized in Railway

---

## 🎯 What We'll Set Up

1. **PostgreSQL Database** - For production data storage
2. **Redis** - For caching and Celery message broker
3. **Django Web Service** - Main application
4. **Celery Worker** - Background task processing
5. **Celery Beat** - Scheduled task management

---

## 📝 Environment Variables to Configure

Once services are created in Railway, configure these variables:

```
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.railway.app

# Database (auto-configured by Railway)
DATABASE_URL=postgresql://...

# Redis (auto-configured by Railway)
REDIS_URL=redis://...

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Razorpay
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret

# Site Configuration
SITE_URL=https://your-domain.railway.app
```

---

## 🚀 Deployment Steps

### Step 1: Create PostgreSQL Service

```bash
# Add PostgreSQL to your project
railway service add PostgreSQL
```

Or use Railway Dashboard:
- Go to https://railway.app/project/YOUR_PROJECT_ID
- Click "Add Service"
- Select "PostgreSQL"

### Step 2: Create Redis Service

```bash
# Add Redis to your project
railway service add Redis
```

Or use Railway Dashboard:
- Click "Add Service"
- Select "Redis"

### Step 3: Deploy Django Application

```bash
# Push your code to Railway
railway up

# Or deploy using GitHub
# Go to Railway Dashboard → Connect GitHub repository
```

### Step 4: Configure Environment Variables

```bash
# Set required environment variables
railway variables set DEBUG False
railway variables set ALLOWED_HOSTS your-domain.railway.app

# Email configuration
railway variables set EMAIL_BACKEND django.core.mail.backends.smtp.EmailBackend
railway variables set EMAIL_HOST smtp.gmail.com
railway variables set EMAIL_PORT 587
railway variables set EMAIL_HOST_USER your-email@gmail.com
railway variables set EMAIL_HOST_PASSWORD your-app-password

# Razorpay
railway variables set RAZORPAY_KEY_ID your_key_id
railway variables set RAZORPAY_KEY_SECRET your_key_secret

# Site URL
railway variables set SITE_URL https://your-domain.railway.app
```

### Step 5: Run Database Migrations

```bash
# SSH into the web service and run migrations
railway shell

# Inside the container:
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

Or use the Railway Dashboard:
- Click the service
- Go to Logs/Shell
- Run migration commands

### Step 6: Add Celery Worker (Optional but Recommended)

Create a new service for Celery worker:
```bash
railway service add
# Choose Custom
# Name: celery-worker
# Command: celery -A moviebooking worker -l info
```

### Step 7: Add Celery Beat (Optional but Recommended)

Create a new service for Celery Beat:
```bash
railway service add
# Choose Custom
# Name: celery-beat
# Command: celery -A moviebooking beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## 📊 Configuration Files

The following files have been created for Railway deployment:

### 1. **Dockerfile**
- Uses Python 3.13 slim image
- Installs PostgreSQL client and build tools
- Collects static files
- Runs migrations on startup

### 2. **Procfile**
- Web service: Gunicorn with 3 workers
- Worker service: Celery worker
- Beat service: Celery Beat scheduler

### 3. **railway.json**
- Build configuration
- Deploy command with migrations

### 4. **requirements.txt**
- All Python dependencies
- Includes `dj-database-url` for PostgreSQL support

---

## 🔗 Database Connection

Railway automatically provides:
- `DATABASE_URL` for PostgreSQL connection
- `REDIS_URL` for Redis connection

The Django settings are configured to:
1. Check for `DATABASE_URL` environment variable
2. If present, use PostgreSQL via `dj-database-url`
3. If not present, fall back to SQLite (development)

---

## 📝 Django Settings for Production

Key settings already configured:

```python
# Database - Auto switches based on DATABASE_URL
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

# Redis - Uses REDIS_URL from Railway
REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')

# Celery - Configured for async tasks
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = 'django-db'

# Email - SMTP in production
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
```

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Set `DEBUG=False` in Railway
- [ ] Configure `SECRET_KEY` with a secure random value
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Configure email SMTP credentials
- [ ] Configure Razorpay credentials
- [ ] Enable HTTPS (Railway provides this)
- [ ] Set up database backups
- [ ] Configure monitoring and logging

---

## 🧪 Testing Deployment

### Check Application Health

```bash
# Check if application is running
curl https://your-domain.railway.app

# Check Django admin
https://your-domain.railway.app/admin/

# Check API endpoints
https://your-domain.railway.app/api/movies/
```

### Check Services

```bash
# View logs
railway logs

# View environment variables
railway variables

# View all services
railway services
```

---

## 📊 Monitoring

Railway provides built-in monitoring:

1. **Logs** - View application and service logs
2. **Metrics** - CPU, Memory, Network usage
3. **Deployments** - View deployment history
4. **Integrations** - Connect monitoring services

Access these in Railway Dashboard under your project.

---

## 🔄 Continuous Deployment

### GitHub Integration

1. Go to Railway Dashboard
2. Click "Connect GitHub"
3. Select your repository
4. Enable auto-deploy on push to `main` branch

### Environment-Specific Deployments

```bash
# Deploy to production
git push origin main

# Railway will automatically:
# 1. Build Docker image
# 2. Run migrations
# 3. Collect static files
# 4. Start services
```

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check DATABASE_URL
railway variables | grep DATABASE

# Test connection
railway shell
python manage.py dbshell
```

### Redis Connection Issues

```bash
# Check REDIS_URL
railway variables | grep REDIS

# Test connection
redis-cli -u $REDIS_URL ping
```

### Static Files Not Loading

```bash
# Recollect static files
railway shell
python manage.py collectstatic --noinput --clear

# Check STATIC_ROOT and STATIC_URL in settings
```

### Migrations Not Running

```bash
# Run migrations manually
railway shell
python manage.py migrate --no-input
```

---

## 📝 Important Notes

### Memory and CPU

Railway provides:
- 512MB RAM on free tier
- Scales up as needed
- Monitor usage in Dashboard

### Persistent Data

- PostgreSQL: Persistent across deployments
- Redis: Persistent (backup regularly)
- Uploaded files: Store in external storage (S3 recommended)

### Cost Optimization

- Use PostgreSQL instead of SQLite
- Enable connection pooling
- Use Redis for caching
- Monitor resource usage

---

## 🎯 Next Steps

1. ✅ Review this guide
2. ✅ Create PostgreSQL service in Railway
3. ✅ Create Redis service in Railway
4. ✅ Deploy application
5. ✅ Configure environment variables
6. ✅ Run migrations
7. ✅ Test application
8. ✅ Set up monitoring
9. ✅ Configure backups

---

## 📞 Getting Help

### Railway Documentation
- https://docs.railway.app
- https://railway.app/help

### Django Documentation
- https://docs.djangoproject.com
- https://docs.djangoproject.com/en/5.2/howto/deployment/

### Troubleshooting
- Check Railway logs: `railway logs`
- Check Django logs: Application logs in Railway Dashboard
- Check PostgreSQL: `railway shell` → `python manage.py dbshell`
- Check Redis: Railway Dashboard → Redis service logs

---

## ✅ Deployment Checklist

- [ ] Dockerfile created
- [ ] Procfile configured
- [ ] railway.json created
- [ ] requirements.txt updated with `dj-database-url`
- [ ] Django settings updated for PostgreSQL
- [ ] Railway project initialized
- [ ] PostgreSQL service added
- [ ] Redis service added
- [ ] Environment variables configured
- [ ] Migrations run
- [ ] Super user created
- [ ] Static files collected
- [ ] Application tested
- [ ] Domain configured (if using custom domain)
- [ ] Monitoring enabled

---

**Status**: ✅ Ready for Deployment  
**Last Updated**: January 16, 2026  
**Version**: 1.0

