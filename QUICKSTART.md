# 🚀 Quick Start - After Deployment

Your application is now live! Here's what to do next.

---

## 🌍 Access Your Application

```
🔗 https://moviebookingapp-production-0bce.up.railway.app
```

---

## 📋 First 5 Minutes

### 1. Update ALLOWED_HOSTS (IMPORTANT!)
```bash
railway variables --set "ALLOWED_HOSTS=moviebookingapp-production-0bce.up.railway.app"
```

### 2. Create Admin User
```bash
railway ssh -- python manage.py createsuperuser
```
Then visit: `https://moviebookingapp-production-0bce.up.railway.app/admin/`

### 3. Test API
```bash
curl https://moviebookingapp-production-0bce.up.railway.app/api/movies/
```

### 4. Add Email (Optional)
```bash
railway variables \
  --set "EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend" \
  --set "EMAIL_HOST=smtp.gmail.com" \
  --set "EMAIL_HOST_USER=your-email@gmail.com" \
  --set "EMAIL_HOST_PASSWORD=your-app-password"
```

### 5. Add Razorpay Keys (For Real Payments)
```bash
railway variables \
  --set "RAZORPAY_KEY_ID=your_key_id" \
  --set "RAZORPAY_KEY_SECRET=your_key_secret"
```

---

## 🔍 Check Status

```bash
# View logs
railway logs --tail 20

# Check all services
railway service status

# View variables
railway variables
```

---

## 🎯 Services Running

| Service | Status | Endpoint |
|---------|--------|----------|
| Django App | ✅ Running | https://moviebookingapp-production-0bce.up.railway.app |
| PostgreSQL | ✅ Running | postgres.railway.internal:5432 |
| Redis | ✅ Running | redis.railway.internal:6379 |

---

## 🔑 Key Features Available

✅ User authentication  
✅ Movie browsing  
✅ Seat selection  
✅ Booking management  
✅ Admin dashboard  
✅ REST API  

---

## 📞 Common Commands

```bash
# View recent logs
railway logs --tail 50

# Connect to database
railway ssh --service Postgres

# Connect to app
railway ssh

# Run Django command
railway ssh -- python manage.py migrate

# Redeploy
railway redeploy --service movie_booking_app

# Set environment variable
railway variables --set "KEY=value"
```

---

## 🎓 Important Files

- `DEPLOYMENT_SUMMARY.md` - Detailed deployment info
- `RAILWAY_DEPLOYMENT_GUIDE.md` - Step-by-step guide
- `RAILWAY_CLI_REFERENCE.md` - All CLI commands

---

## ⚡ Performance Tips

1. **Enable caching** - Redis is ready
2. **Setup email** - For notifications
3. **Add Razorpay keys** - For real payments
4. **Monitor logs** - Check `railway logs` regularly

---

## 🔒 Security Reminders

- ✅ DEBUG is False
- ✅ HTTPS is enabled
- ⚠️ Update SECRET_KEY
- ⚠️ Update ALLOWED_HOSTS
- ⚠️ Add email credentials
- ⚠️ Add payment credentials

---

## 🆘 If Something Goes Wrong

```bash
# Check logs
railway logs --tail 100 | grep -i error

# SSH and investigate
railway ssh

# Redeploy
railway redeploy --service movie_booking_app

# Contact Railway support
https://railway.app/help
```

---

## ✨ You're All Set!

Your movie booking system is live and ready to use. Enjoy! 🎬

---

**Status**: ✅ DEPLOYED  
**URL**: https://moviebookingapp-production-0bce.up.railway.app  
**Services**: Django + PostgreSQL + Redis
