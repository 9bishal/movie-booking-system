# Railway Deployment Checklist

## ✅ Pre-Deployment Checklist

### Code & Dependencies
- [x] `requirements.txt` cleaned and minimal (52 packages)
- [x] `requirements-production.txt` references main requirements
- [x] Django 4.2.0 (compatible with Celery)
- [x] Razorpay 2.0.0 (correct version)
- [x] All dependencies install without errors
- [x] `Procfile` configured correctly
- [x] `Dockerfile` present
- [x] `railway.json` present
- [x] `.gitignore` excludes `.env` and `*.db`

### Django Settings
- [x] `moviebooking/settings_production.py` created
- [x] `DEBUG=False` for production
- [x] `SECRET_KEY` set to strong value
- [x] `ALLOWED_HOSTS` set for Railway
- [x] `DATABASES` uses `DATABASE_URL` env variable
- [x] `CACHES` uses `REDIS_URL` env variable
- [x] Email backend configured
- [x] Static files configured with WhiteNoise
- [x] Security settings enabled
- [x] CSRF and CORS settings configured

### Testing
- [x] `python manage.py check` passes
- [x] `python manage.py check --deploy` passes
- [x] Tests run (60/62 passing)
- [x] `python manage.py collectstatic` works
- [x] Static files collected successfully

### Git & GitHub
- [ ] Code pushed to GitHub main branch
- [ ] `.env` file NOT committed
- [ ] All files committed

## 🚀 Railway Deployment Steps

### Step 1: Push to GitHub
```bash
cd /Users/bishalkumarshah/.gemini/antigravity/scratch/movie-booking-system
git add .
git commit -m "Ready for Railway deployment: Clean dependencies, production settings"
git push origin main
```

### Step 2: Create Railway Account
- [ ] Go to https://railway.app
- [ ] Sign up with GitHub account
- [ ] Authorize Railway to access your GitHub repos

### Step 3: Create New Project
- [ ] In Railway dashboard, click "New Project"
- [ ] Click "Deploy from GitHub"
- [ ] Select your `movie-booking-system` repository
- [ ] Select `main` branch
- [ ] Click "Deploy"

**Railway will now:**
- Build Docker image
- Install dependencies from `requirements.txt`
- Collect static files automatically
- Start services from `Procfile`

Monitor progress in the Deployments tab.

### Step 4: Add PostgreSQL Database
- [ ] In Railway dashboard, click "Add Service"
- [ ] Search for "PostgreSQL"
- [ ] Click to add PostgreSQL 15
- [ ] Railway auto-creates `DATABASE_URL` env variable
- [ ] Redeploy app to apply changes

### Step 5: Add Redis Cache
- [ ] In Railway dashboard, click "Add Service"
- [ ] Search for "Redis"
- [ ] Click to add Redis 7
- [ ] Railway auto-creates `REDIS_URL` env variable
- [ ] Redeploy app to apply changes

### Step 6: Set Environment Variables
In Railway dashboard, go to your project > Variables tab > Add these:

**Django Core:**
```
DEBUG=False
SECRET_KEY=_6$604vp-8p%p8y$j%txfa@*bzc)v5na6p7h)u135w1hllmo@k
ENVIRONMENT=production
```

**Get domain from Railway, then set:**
```
ALLOWED_HOSTS=your-railway-app-name.up.railway.app
```

**Email (Gmail with App Passwords):**
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=MovieBooking <noreply@moviebooking.com>
EMAIL_USE_TLS=True
```

**Razorpay (from https://dashboard.razorpay.com/app/keys):**
```
RAZORPAY_KEY_ID=your-key-id
RAZORPAY_KEY_SECRET=your-secret-key
```

**Security (recommended):**
```
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

After setting variables:
- [ ] Wait for automatic redeploy
- [ ] Check "Deployments" tab for completion

### Step 7: Run Database Migrations
In Railway dashboard, open terminal and run:

```bash
# Option A: Via Railway Dashboard terminal
python manage.py migrate --settings=moviebooking.settings_production

# Option B: Via Railway CLI
railway run python manage.py migrate --settings=moviebooking.settings_production
```

### Step 8: Create Superuser
```bash
# Option A: Via Railway Dashboard terminal
python manage.py createsuperuser --settings=moviebooking.settings_production

# Option B: Via Railway CLI
railway run python manage.py createsuperuser --settings=moviebooking.settings_production
```

## ✅ Post-Deployment Verification

### Test Core Functionality
- [ ] App loads: Visit `https://your-app-name.up.railway.app`
- [ ] Homepage displays correctly
- [ ] CSS and images load (static files working)
- [ ] Admin panel works: Visit `/admin` with superuser credentials
- [ ] Login page works: Visit `/accounts/login`
- [ ] Can register new user
- [ ] Can browse movies and showtimes
- [ ] Can select seats and book tickets
- [ ] Payment flow works (Razorpay integration)
- [ ] Receives confirmation email

### Check Logs
- [ ] Go to Deployments tab
- [ ] Click latest deployment
- [ ] Check logs for any errors
- [ ] Verify no 500 errors
- [ ] Verify database connection successful

### Database Verification
```bash
# Check database connection
railway run python manage.py dbshell --settings=moviebooking.settings_production
# Type: \dt (to list tables)
# Type: \q (to exit)
```

### Redis Verification
```bash
# Check Redis connection
railway run python manage.py shell --settings=moviebooking.settings_production
# >>> from django.core.cache import cache
# >>> cache.set('test', 'value')
# >>> cache.get('test')
# 'value'
# >>> exit()
```

## 📊 Environment Variables Reference

**Auto-set by Railway:**
```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
PORT=8000
```

**Required by App:**
```
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-app-domain.up.railway.app
ENVIRONMENT=production
```

**Email Config:**
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=MovieBooking <noreply@moviebooking.com>
EMAIL_USE_TLS=True
```

**Payment Gateway:**
```
RAZORPAY_KEY_ID=your-key
RAZORPAY_KEY_SECRET=your-secret
```

**Security:**
```
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

## 🆘 Troubleshooting

### App won't start
1. Check Railway logs: Deployments > Click deployment > Logs
2. Look for error messages
3. Common issues:
   - Missing environment variables
   - DATABASE_URL not set
   - Migrations not run
   - SECRET_KEY not set

### "DATABASE_URL not set"
- Add PostgreSQL service in Railway dashboard
- Wait for auto-redeploy
- Check that DATABASE_URL appears in Variables

### "REDIS_URL not set"
- Add Redis service in Railway dashboard
- Wait for auto-redeploy
- Check that REDIS_URL appears in Variables

### Static files not loading
- Check Railway logs for collectstatic errors
- Verify whitenoise is installed: `pip list | grep whitenoise`
- Redeploy: Push a commit to GitHub
- Clear Railway cache (if option available)

### Email not sending
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in Variables
- Use Gmail App Passwords, not regular password
- Check spam folder
- Test with Django shell:
  ```bash
  railway run python manage.py shell --settings=moviebooking.settings_production
  from django.core.mail import send_mail
  send_mail('Test', 'Hello', 'from@gmail.com', ['to@gmail.com'])
  ```

### Migrations not running
```bash
# Check migration status
railway run python manage.py showmigrations --settings=moviebooking.settings_production

# Run pending migrations
railway run python manage.py migrate --settings=moviebooking.settings_production
```

## 📈 Monitoring & Maintenance

### Regular Checks
- [ ] Monitor Railway logs daily
- [ ] Check database storage usage
- [ ] Monitor Redis memory usage
- [ ] Watch for repeated error patterns
- [ ] Monitor app response times

### Useful Commands
```bash
# View logs
railway logs

# View environment variables
railway variables

# Update variable
railway variables set KEY=newvalue

# Run Django command
railway run python manage.py COMMAND

# Access Django shell
railway run python manage.py shell --settings=moviebooking.settings_production

# Database backup (if needed)
railway run python manage.py dumpdata > backup.json

# Restore from backup
railway run python manage.py loaddata backup.json
```

## 🔄 Updating Your App

To deploy new code changes:

```bash
# 1. Make changes locally
# 2. Test thoroughly
# 3. Commit and push
git add .
git commit -m "Feature: Add feature description"
git push origin main

# 4. Railway automatically redeploys
# 5. Monitor in Railway dashboard
# 6. If models changed, run migrations:
railway run python manage.py migrate --settings=moviebooking.settings_production
```

## 💾 Backup Strategy

```bash
# Backup database
railway run python manage.py dumpdata --settings=moviebooking.settings_production > backup-$(date +%Y%m%d).json

# Backup media files (if using S3, backup to local)
# Backup environment variables (export from Railway dashboard)

# Store backups in:
# - GitHub (for code backups)
# - AWS S3 (for database/media backups)
# - Local storage (for disaster recovery)
```

## 🎯 Success Criteria

Your deployment is successful when:

✅ App is live and accessible  
✅ Homepage loads without errors  
✅ Database connection working  
✅ Can login and register users  
✅ Can browse movies and showtimes  
✅ Can book tickets and make payments  
✅ Emails sending correctly  
✅ Admin panel fully functional  
✅ Static files (CSS, images) loading  
✅ No errors in Railway logs  
✅ App responds within 2 seconds  
✅ Can scale to multiple requests  

---

**Status**: ✅ Complete Deployment Checklist
**Last Updated**: 8 January 2026
**Railway Deployment**: Ready to Go 🚀
