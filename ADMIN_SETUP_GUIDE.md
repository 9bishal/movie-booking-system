# Railway Production - Admin Access Setup Guide

This guide will help you create and access admin accounts in Railway production.

---

## 🚀 Quick Setup (Recommended)

### Option 1: Using Railway CLI (Fastest)

1. **Install Railway CLI** (if not installed):
   ```bash
   npm i -g @railway/cli
   ```

2. **Run the setup script**:
   ```bash
   chmod +x setup_railway_admin.sh
   ./setup_railway_admin.sh
   ```

3. **Done!** Your admin user is created and ready to use.

---

## 🔧 Manual Setup Methods

### Option 2: Using Railway Web Dashboard

1. **Open Railway Dashboard**
   - Go to: https://railway.app/
   - Select your project: `movie-booking-system`
   - Click on your Django service

2. **Open Terminal**
   - Click on "Terminal" tab in the service dashboard
   - Wait for the terminal to connect

3. **Run Management Command**
   ```bash
   python manage.py create_admin --username admin --email admin@moviebooking.com --password admin123 --reset
   ```

4. **Done!** Your admin credentials will be displayed.

---

### Option 3: Using Railway CLI (Manual)

1. **Link to your project**:
   ```bash
   railway link
   ```

2. **Run the management command**:
   ```bash
   railway run python manage.py create_admin --username admin --email admin@moviebooking.com --password admin123 --reset
   ```

3. **Done!** Your admin user is created.

---

## 📋 Admin Access URLs

After creating the admin user, you can access:

### Django Admin (Built-in)
- **URL**: `https://your-app.railway.app/admin/`
- **Features**: Full Django admin interface with all models
- **Login**: Use your admin credentials

### Custom Admin Dashboard
- **URL**: `https://your-app.railway.app/custom-admin/`
- **Features**: Beautiful custom dashboard with analytics, charts, and booking management
- **Login**: Use your admin credentials

---

## 🔑 Default Credentials

If you used the default settings:
- **Username**: `admin`
- **Email**: `admin@moviebooking.com`
- **Password**: `admin123`

⚠️ **Change these in production!**

---

## ⚙️ Management Command Options

The `create_admin` command supports several options:

```bash
# Create with custom credentials
python manage.py create_admin --username myadmin --email admin@example.com --password mysecurepass

# Reset existing admin user
python manage.py create_admin --reset

# Reset with new credentials
python manage.py create_admin --username admin --email newemail@example.com --password newpass --reset
```

---

## ✅ Verification Steps

After creating the admin user, verify:

1. **Staff Status**: ✅ is_staff = True
2. **Superuser**: ✅ is_superuser = True
3. **Active**: ✅ is_active = True
4. **Email Verified**: ✅ is_email_verified = True

All of these are automatically set by the management command.

---

## 🐛 Troubleshooting

### Problem: "User already exists" error
**Solution**: Use the `--reset` flag to update the existing user
```bash
python manage.py create_admin --reset
```

### Problem: "Module not found" error
**Solution**: Ensure you're in the correct directory
```bash
cd /path/to/movie-booking-system
python manage.py create_admin --reset
```

### Problem: Can't access Railway terminal
**Solution**: Use Railway CLI instead:
```bash
railway login
railway link
railway run python manage.py create_admin --reset
```

### Problem: Admin login fails
**Solution**: Reset the password using the command:
```bash
railway run python manage.py create_admin --username admin --password newpassword --reset
```

---

## 🔒 Security Best Practices

1. **Change default password** immediately in production
2. **Use strong passwords** (at least 12 characters)
3. **Enable 2FA** if possible (via Django admin)
4. **Limit admin access** to trusted IPs if possible
5. **Regularly audit** admin user activity

---

## 📝 Additional Commands

### List all admin users
```bash
railway run python manage.py shell -c "from django.contrib.auth.models import User; print([u.username for u in User.objects.filter(is_staff=True)])"
```

### Verify admin email for all staff
```bash
railway run python manage.py verify_admin_emails
```

### Check user details
```bash
railway run python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='admin'); print(f'Staff: {u.is_staff}, Super: {u.is_superuser}, Active: {u.is_active}')"
```

---

## 🎯 What's Fixed

This admin setup ensures:

- ✅ **Proper Staff Status**: `is_staff=True` for Django admin access
- ✅ **Superuser Permissions**: `is_superuser=True` for full access
- ✅ **Active Account**: `is_active=True` for login
- ✅ **Email Verified**: `is_email_verified=True` (bypasses verification)
- ✅ **Profile Created**: Automatic UserProfile creation with verification
- ✅ **Password Set**: Properly hashed password
- ✅ **No Duplicates**: Safe reset of existing users

---

## 🚀 Quick Test

After setup, test admin access:

1. **Django Admin**: https://your-app.railway.app/admin/
2. **Custom Admin**: https://your-app.railway.app/custom-admin/
3. **Login with your credentials**
4. **Verify you can see all models and dashboards**

---

## 📧 Need Help?

If you encounter any issues:
1. Check Railway logs: `railway logs`
2. Check database connectivity
3. Verify environment variables are set
4. Try the reset command again

---

## ✨ Summary

The easiest way to set up admin access:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Run setup script
chmod +x setup_railway_admin.sh
./setup_railway_admin.sh
```

That's it! Your admin user is ready to use. 🎉
