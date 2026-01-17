# ✅ Week 4 Deployment Checklist

Complete this checklist before deploying to production.

---

## Phase 1: Testing (Days 22-23) ✅ COMPLETE

- [x] Unit tests written (53 tests)
- [x] All tests passing
- [x] Code coverage reviewed
- [x] Bug fixes applied
- [x] Authentication tests pass
- [x] Payment tests pass
- [x] Booking tests pass
- [x] Edge cases covered
- [x] Security tests pass
- [x] Concurrent operation tests pass

**Status**: ✅ COMPLETE - 53/53 tests passing

---

## Phase 2: Pre-Deployment (Days 24-26)

### 2.1 Code Quality

- [ ] No console.log() left in code
- [ ] No TODO comments without issues
- [ ] Code follows PEP 8 standards
- [ ] All imports are used
- [ ] No circular imports
- [ ] Type hints added to critical functions
- [ ] Docstrings complete
- [ ] Comments explain WHY, not WHAT

**Check**:
```bash
# Run linting
flake8 . --exclude=venv,migrations
pylint bookings/ accounts/ movies/
```

### 2.2 Security Review

- [ ] DEBUG = False in production settings ✅
- [ ] SECRET_KEY is strong and not exposed ✅
- [ ] ALLOWED_HOSTS configured ✅
- [ ] HTTPS enabled (Heroku provides this)
- [ ] CSRF protection enabled
- [ ] SQL injection protection verified
- [ ] XSS protection enabled
- [ ] No hardcoded credentials in code
- [ ] Environment variables used for secrets
- [ ] .env file in .gitignore
- [ ] No sensitive data in logs
- [ ] Password hashing verified (Django default)
- [ ] Session security configured
- [ ] Cookie security configured

**Check**:
```bash
# Security check
python manage.py check --deploy --settings=moviebooking.settings_production
```

### 2.3 Database Setup

- [ ] Migrations created for all models
- [ ] Migration files reviewed
- [ ] Database schema correct
- [ ] Indexes created for performance
- [ ] Foreign key relationships verified
- [ ] No NULL constraints issues
- [ ] Default values appropriate
- [ ] PostgreSQL tested locally

**Check**:
```bash
# Check migrations
python manage.py showmigrations
python manage.py migrate --plan

# Test PostgreSQL locally
# Use docker-compose.yml to run PostgreSQL container
docker-compose up db -d
```

### 2.4 Static Files & Media

- [ ] Static files collected
- [ ] CSS/JS minified
- [ ] Images optimized
- [ ] Media upload directory configured
- [ ] File upload security (whitelist extensions)
- [ ] Disk space plan for uploads
- [ ] CDN/S3 configured (if using)
- [ ] Static files served correctly

**Check**:
```bash
python manage.py collectstatic --noinput
```

### 2.5 Email Configuration

- [ ] Email backend configured
- [ ] SMTP credentials set
- [ ] Email templates tested
- [ ] No hardcoded email addresses
- [ ] Email logging configured
- [ ] Error handling in email tasks
- [ ] Bounce/complaint handling (if using SendGrid)
- [ ] Email rate limiting considered

**Check**:
```bash
# Test email locally
python manage.py shell
from django.core.mail import send_mail
send_mail('Test Subject', 'Test Body', 'from@example.com', ['to@example.com'])
```

### 2.6 Payment Gateway (Razorpay)

- [ ] API keys obtained (test & production)
- [ ] Webhook configured
- [ ] Webhook secret stored securely
- [ ] Payment flow tested (test cards provided by Razorpay)
- [ ] Refund logic implemented
- [ ] Timeout handling implemented
- [ ] Error handling comprehensive
- [ ] Payment logging secure (no sensitive data)
- [ ] Idempotency implemented (prevent duplicate charges)

**Check**:
```bash
# Verify Razorpay keys
heroku config | grep RAZORPAY
```

### 2.7 Celery & Redis

- [ ] Redis installation verified
- [ ] Celery broker configured
- [ ] Celery result backend configured
- [ ] Task queues defined
- [ ] Task timeouts set
- [ ] Error handling in tasks
- [ ] Retry logic implemented
- [ ] Dead letter queue configured
- [ ] Worker concurrency configured
- [ ] Beat scheduler for periodic tasks (optional)

**Check**:
```bash
# Test Celery
python manage.py shell
from bookings.tasks import send_confirmation_email
send_confirmation_email.delay(booking_id)

# Check task status
python manage.py celery_inspect active
```

### 2.8 Performance Optimization

- [ ] Database queries optimized (select_related, prefetch_related)
- [ ] N+1 query problem solved
- [ ] Indexes created for foreign keys
- [ ] Cache configured
- [ ] Cache keys documented
- [ ] Cache invalidation logic correct
- [ ] API response times acceptable (<500ms)
- [ ] Page load times acceptable (<2s)
- [ ] Large file handling optimized
- [ ] Memory leaks checked

**Check**:
```bash
# Django Debug Toolbar for local testing
pip install django-debug-toolbar
# Enable in development settings
```

### 2.9 Monitoring & Logging

- [ ] Logging configured
- [ ] Log files rotate
- [ ] Error tracking setup (Sentry recommended)
- [ ] Application metrics tracked
- [ ] Database performance monitored
- [ ] Error alerts configured
- [ ] Uptime monitoring configured
- [ ] Backup strategy documented
- [ ] Recovery procedure documented

**Check**:
```bash
# Test logging
python manage.py shell
import logging
logger = logging.getLogger(__name__)
logger.error('Test error message')
```

---

## Phase 3: Deployment to Heroku (Days 24-26)

### 3.1 Heroku Setup

- [ ] Heroku account created
- [ ] Heroku CLI installed
- [ ] GitHub connected to Heroku (optional, for auto-deploy)
- [ ] App name chosen (available)
- [ ] Region selected (us for US, eu for Europe)

**Setup**:
```bash
# Login and create app
heroku login
heroku create your-app-name --region us
```

### 3.2 Add-ons & Services

- [ ] Heroku PostgreSQL add-on added
  ```bash
  heroku addons:create heroku-postgresql:standard-0
  ```

- [ ] Heroku Redis add-on added
  ```bash
  heroku addons:create heroku-redis:premium-0
  ```

- [ ] Environment variables set
  ```bash
  heroku config:set DEBUG=False
  heroku config:set ALLOWED_HOSTS=your-app.herokuapp.com
  heroku config:set SECRET_KEY='very-long-random-string'
  heroku config:set EMAIL_HOST=smtp.gmail.com
  heroku config:set EMAIL_HOST_USER=your-email@gmail.com
  heroku config:set EMAIL_HOST_PASSWORD=your-app-password
  heroku config:set RAZORPAY_KEY_ID=your-key
  heroku config:set RAZORPAY_KEY_SECRET=your-secret
  ```

- [ ] Verify configuration
  ```bash
  heroku config
  ```

### 3.3 Code Deployment

- [ ] All code committed to git
  ```bash
  git add .
  git commit -m "Week 4: Testing, deployment files, production setup"
  ```

- [ ] Git remote added
  ```bash
  git remote add heroku https://git.heroku.com/your-app.git
  ```

- [ ] Code pushed to Heroku
  ```bash
  git push heroku main
  ```

- [ ] Build logs checked for errors
  ```bash
  heroku logs --tail
  ```

### 3.4 Database Migration

- [ ] Migrations run
  ```bash
  heroku run python manage.py migrate
  ```

- [ ] Sample data loaded (optional)
  ```bash
  heroku run python manage.py loaddata initial_data
  ```

- [ ] Superuser created
  ```bash
  heroku run python manage.py createsuperuser
  ```

- [ ] Database verified
  ```bash
  heroku pg:info
  ```

### 3.5 Static Files

- [ ] Static files collected
  ```bash
  python manage.py collectstatic --noinput --settings=moviebooking.settings_production
  git add . && git commit -m "Collect static files"
  git push heroku main
  ```

- [ ] Assets accessible
  ```bash
  heroku open  # Check /static/ and /media/ paths
  ```

### 3.6 Process Management

- [ ] Web dyno configured
  ```bash
  heroku ps:scale web=1
  ```

- [ ] Worker dyno configured
  ```bash
  heroku ps:scale worker=1
  ```

- [ ] Beat dyno configured (optional, for scheduled tasks)
  ```bash
  heroku ps:scale beat=1
  ```

- [ ] Process status checked
  ```bash
  heroku ps
  ```

---

## Phase 4: Post-Deployment Verification

### 4.1 Application Functionality

- [ ] Homepage loads without error
  ```
  heroku open
  ```

- [ ] User registration works
  - Create new account
  - Verify email received
  - Verify account activated

- [ ] User login works
  - Login with correct credentials
  - Logout works
  - Session management correct

- [ ] Movie browsing works
  - Movie list displays
  - Movie detail page loads
  - Filtering/search works

- [ ] Booking creation works
  - Can select showtime
  - Can select seats
  - Price calculation correct
  - Can proceed to payment

- [ ] Payment flow works
  - Razorpay modal opens
  - Test payment succeeds
  - Confirmation email received
  - Booking marked as confirmed

- [ ] Admin panel works
  - Can login to /admin
  - Can view bookings
  - Can modify data

### 4.2 Background Jobs

- [ ] Celery worker running
  ```bash
  heroku ps | grep worker
  heroku logs --tail -p worker
  ```

- [ ] Tasks executing
  - Check logs for task executions
  - Verify email sending
  - Verify data processing

- [ ] Celery Beat running (if configured)
  ```bash
  heroku ps | grep beat
  ```

- [ ] Periodic tasks executing

### 4.3 Monitoring & Logging

- [ ] Logs accessible
  ```bash
  heroku logs --tail
  heroku logs -n 50 -p web
  heroku logs -n 50 -p worker
  ```

- [ ] No error stack traces in logs
- [ ] Performance acceptable
  ```bash
  heroku metrics
  ```

- [ ] Database health check
  ```bash
  heroku pg:info
  ```

- [ ] Redis cache operational
  ```bash
  heroku redis:info
  ```

---

## Phase 5: Security Hardening (Post-Deployment)

- [ ] HTTPS enforced
  ```bash
  heroku config:set SECURE_SSL_REDIRECT=True
  heroku config:set SESSION_COOKIE_SECURE=True
  heroku config:set CSRF_COOKIE_SECURE=True
  ```

- [ ] Security headers set
  ```python
  SECURE_HSTS_SECONDS = 31536000
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  ```

- [ ] Rate limiting enabled (optional)
  - Install django-ratelimit
  - Configure limits on sensitive endpoints

- [ ] CORS configured (if API)
  ```bash
  heroku config:set CORS_ALLOWED_ORIGINS='["https://yourdomain.com"]'
  ```

- [ ] Error tracking configured (Sentry)
  ```bash
  heroku config:set SENTRY_DSN='your-sentry-url'
  ```

---

## Phase 6: Backup & Disaster Recovery

- [ ] Database backup scheduled
  ```bash
  heroku pg:backups:schedule DATABASE_URL --at '02:00 UTC'
  ```

- [ ] First backup created
  ```bash
  heroku pg:backups:capture
  heroku pg:backups
  ```

- [ ] Backup verified (test restore in staging)
  ```bash
  heroku pg:backups:restore b001 DATABASE_URL --confirm your-app-name
  ```

- [ ] Recovery procedure documented
- [ ] Contact list updated

---

## Phase 7: Documentation & Handoff

- [ ] README.md updated with deployment info
- [ ] API documentation complete
- [ ] Deployment guide created (DEPLOYMENT_GUIDE.md) ✅
- [ ] Troubleshooting guide created
- [ ] Database schema documented
- [ ] Environment variables documented
- [ ] Team trained on deployment
- [ ] Access credentials shared securely

---

## Final Verification Checklist

Before declaring done, verify:

- [ ] All 53 tests still passing
- [ ] No console errors in browser
- [ ] No server errors in logs
- [ ] Page load time < 2 seconds
- [ ] Mobile responsive
- [ ] Payment flow works with real card
- [ ] Emails send and arrive
- [ ] Database backups working
- [ ] Error tracking alerting
- [ ] Can scale processes up/down

---

## Known Issues & Workarounds

### Issue: Static files returning 404
**Solution**: 
```bash
python manage.py collectstatic --noinput
git add . && git commit -m "Update static files"
git push heroku main
```

### Issue: Database connection timeout
**Solution**:
```bash
heroku config:set CONN_MAX_AGE=600
# Or increase timeout in settings_production.py
```

### Issue: Worker not processing tasks
**Solution**:
```bash
heroku ps:restart worker
heroku logs --tail -p worker
```

### Issue: Out of memory errors
**Solution**:
```bash
# Upgrade dyno type
heroku dyno:type standard-1x
# Or reduce worker concurrency
heroku config:set CELERYD_CONCURRENCY=2
```

---

## Success Criteria

✅ **Deployment is successful when**:

1. **Application loads** - No 500 errors
2. **Database works** - Can view data
3. **Payments work** - Can complete booking → payment → confirmation
4. **Emails work** - Confirmation emails arrive in inbox
5. **Background jobs work** - Tasks execute in logs
6. **Performance acceptable** - Pages load in < 2 seconds
7. **Security in place** - HTTPS enforced, no exposed credentials
8. **Monitoring active** - Logs visible, errors tracked
9. **Backups working** - Database can be backed up and restored
10. **Team trained** - Everyone knows how to deploy

---

## Post-Launch Maintenance

- [ ] Monitor error rates daily
- [ ] Check logs for warnings
- [ ] Verify backups running
- [ ] Monitor disk usage
- [ ] Review performance metrics
- [ ] Update dependencies monthly
- [ ] Security patches applied promptly
- [ ] User feedback collected
- [ ] Known issues tracked

---

**Last Updated**: 8 January 2026
**Deployment Status**: Ready for Heroku
**Tests Status**: ✅ 53/53 Passing
**Documentation Status**: ✅ Complete

---

## ✅ SQLite Configuration Fix - January 2026

### Issue Fixed
**Problem**: Invalid `init_command` option in SQLite configuration causing TypeError
**Solution**: Replaced with proper signal-based PRAGMA setup for WAL mode

### Local Development - Verification Steps

#### 1. Database Configuration ✅
```bash
python test_database_config.py
```
Expected: All checks pass, WAL mode enabled, 20s timeout

#### 2. Email Functionality ✅
```bash
python test_email_functionalities.py
```
Expected: 10/10 tests pass (100% success rate)

#### 3. Comprehensive System Test ✅
```bash
python test_final_comprehensive.py
```
Expected: 8/8 tests pass (100% success rate)

#### 4. Django System Check ✅
```bash
python manage.py check
```
Expected: "System check identified no issues (0 silenced)."

#### 5. Development Server ✅
```bash
python manage.py runserver
```
Expected: Server starts without errors on http://127.0.0.1:8000/

### Key Changes Summary

#### `moviebooking/settings.py`
- ❌ Removed: Invalid `"init_command": "PRAGMA journal_mode=WAL;"`
- ✅ Added: Signal-based WAL mode setup for SQLite
- ✅ Kept: 20-second timeout for lock handling
- ✅ Enhanced: Better PRAGMA configuration (synchronous=NORMAL)

#### New Test Scripts
- ✅ `test_database_config.py` - Database configuration verification
- ✅ `test_final_comprehensive.py` - Full system test
- ✅ `SQLITE_FIX_SUMMARY.md` - Detailed fix documentation

### Status: ✅ ALL TESTS PASSING

- [x] Database configuration verified
- [x] SQLite WAL mode enabled
- [x] Email functionality working (10/10 tests)
- [x] Comprehensive system test passing (8/8 tests)
- [x] Django system check clean
- [x] Development server starts successfully
- [x] No TypeErrors or database errors
- [x] Production (Railway) unaffected - uses PostgreSQL

**Ready for deployment to Railway.**

