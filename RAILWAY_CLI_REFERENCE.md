# 🚀 Railway CLI Commands - Quick Reference

## 📍 Current Deployment Status

```
Application: movie_booking_system
Environment: production
Project: movie_booking_app
URL: https://moviebookingapp-production-0bce.up.railway.app
```

---

## 🔑 Authentication

```bash
# Login to Railway
railway login --browserless

# Logout
railway logout
```

---

## 📦 Service Management

### View All Services

```bash
railway service status
```

### Link to a Service

```bash
railway service link <service-name>
# Example:
railway service link movie_booking_app
railway service link Postgres
railway service link Redis
```

### Add New Service

```bash
# Add Database
railway add --database postgres     # PostgreSQL
railway add --database redis        # Redis
railway add --database mysql        # MySQL
railway add --database mongo        # MongoDB

# Add from Docker Image
railway add --image python:3.11     # Custom Docker image

# Add GitHub Repo
railway add --repo owner/repo-name
```

---

## 🚀 Deployment

### Deploy/Redeploy

```bash
# Deploy current code
railway up

# Redeploy latest (no code changes)
railway redeploy --service movie_booking_app

# Deploy specific service
railway redeploy --service Postgres
```

---

## 📊 Environment Variables

### View Variables

```bash
# View all variables for current service
railway variables

# View in KV format
railway variables --kv

# View as JSON
railway variables --json

# View for specific service
railway variables --service movie_booking_app
```

### Set Variables

```bash
# Set single variable
railway variables --set "DEBUG=False"

# Set multiple variables
railway variables --set "DEBUG=False" --set "ALLOWED_HOSTS=*"

# Set without redeploying
railway variables --set "KEY=value" --skip-deploys
```

### Common Variables Set

```bash
# Production Settings
railway variables --set "DEBUG=False"
railway variables --set "ALLOWED_HOSTS=yourdomain.com"

# Email (SMTP)
railway variables --set "EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend"
railway variables --set "EMAIL_HOST=smtp.gmail.com"
railway variables --set "EMAIL_PORT=587"
railway variables --set "EMAIL_USE_TLS=True"
railway variables --set "EMAIL_HOST_USER=your-email@gmail.com"
railway variables --set "EMAIL_HOST_PASSWORD=your-app-password"

# Razorpay
railway variables --set "RAZORPAY_KEY_ID=your_key_id"
railway variables --set "RAZORPAY_KEY_SECRET=your_key_secret"
```

---

## 📝 Logs

### View Logs

```bash
# View recent logs (tail)
railway logs --tail 50

# View all logs
railway logs

# View logs for specific service
railway logs --service Postgres
railway logs --service Redis

# Stream logs (follow)
railway logs --tail 10 --follow
```

---

## 🌐 Domain Management

### Create/View Domain

```bash
# Create Railway subdomain
railway domain

# View domain
railway status
```

---

## 🔌 Remote Shell Access

### Connect to Service

```bash
# SSH into current service
railway ssh

# SSH into specific service
railway ssh --service movie_booking_app

# Run command directly
railway ssh -- python manage.py createsuperuser
railway ssh -- python manage.py migrate
railway ssh -- python manage.py shell
```

---

## 💾 Database Operations

### Connect to PostgreSQL

```bash
# Open database shell
railway shell
# Then type: psql

# Or directly:
railway ssh --service Postgres
```

### Run Django Management Commands

```bash
railway ssh -- python manage.py migrate
railway ssh -- python manage.py createsuperuser
railway ssh -- python manage.py collectstatic
railway ssh -- python manage.py shell
```

---

## 🔍 Project Information

### View Project Details

```bash
# Current status
railway status

# Service status
railway service status

# View all services
railway service status

# Project information
railway list
```

---

## 🔗 Link/Switch Projects

```bash
# Link to existing project
railway link -p movie_booking_app

# View linked project
railway status

# Create new project
railway init
```

---

## 📤 Code Updates

### Deploy Updated Code

```bash
# Deploy code from current directory
railway up

# Deploy specific branch
git push origin main
# (if using GitHub integration)
```

---

## 🧹 Cleanup Commands

### Remove Service

```bash
# Note: This must be done via Railway Dashboard
# CLI doesn't have service removal command
```

### Clear Cache (if available)

```bash
# Restart service (forces cache clear)
railway redeploy --service movie_booking_app
```

---

## 📊 Metrics & Monitoring

### View Logs

```bash
# Error logs
railway logs | grep -i error

# Deployment logs
railway logs --tail 100
```

### Check Service Health

```bash
railway service status
```

---

## 🎯 Common Workflows

### Initial Setup

```bash
# 1. Login
railway login --browserless

# 2. Link to project
railway link -p movie_booking_app

# 3. Add database
railway add --database postgres

# 4. Add Redis
railway add --database redis

# 5. Set variables
railway variables --set "DEBUG=False"
railway variables --set "ALLOWED_HOSTS=*"

# 6. Deploy
railway up

# 7. Check status
railway logs --tail 20
```

### Deploy Changes

```bash
# 1. Make code changes locally
# 2. Push to Git
git add .
git commit -m "message"
git push origin main

# 3. Redeploy
railway redeploy --service movie_booking_app

# 4. Check logs
railway logs --tail 20
```

### Run Database Migration

```bash
# 1. SSH into service
railway ssh

# 2. Run migration
python manage.py migrate

# 3. Exit
exit
```

### Create Superuser

```bash
railway ssh -- python manage.py createsuperuser
```

---

## 🔐 Security Notes

### Environment Variable Security

```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use Railway CLI to set sensitive variables
railway variables --set "SECRET_KEY=very-secret-key"
```

### Database Connection

```bash
# Always use internal URL in production
# Internal: postgres.railway.internal:5432
# External: switchyard.proxy.rlwy.net:49626
```

---

## 📚 Help Commands

```bash
# General help
railway --help

# Specific command help
railway add --help
railway variables --help
railway service --help
railway logs --help
railway ssh --help
```

---

## 🎓 Useful Tips

### Tip 1: Service Linking
When you link to a different service, all `railway` commands apply to that service:
```bash
railway service link movie_booking_app  # Now commands apply to app
railway variables                        # Shows app variables
railway logs                             # Shows app logs

railway service link Postgres            # Switch to database
railway variables                        # Shows database variables
```

### Tip 2: Multiple Variables
Set multiple variables at once:
```bash
railway variables \
  --set "VAR1=value1" \
  --set "VAR2=value2" \
  --set "VAR3=value3" \
  --skip-deploys
```

### Tip 3: Check Recent Logs
```bash
railway logs --tail 50 | tail -20  # Last 20 lines from 50 lines
```

### Tip 4: SSH Commands
Run commands without entering shell:
```bash
railway ssh -- python manage.py migrate
railway ssh -- python manage.py createsuperuser
```

---

## 🚨 Troubleshooting

### Application Won't Start

```bash
# Check logs
railway logs --tail 100

# SSH and check
railway ssh

# View deployment status
railway service status
```

### Database Connection Issues

```bash
# SSH into database service
railway service link Postgres
railway ssh

# Test connection
psql
\l  # List databases
\q  # Quit
```

### Environment Variable Issues

```bash
# View all variables
railway variables --json

# Set missing variable
railway variables --set "MISSING_VAR=value"
```

---

**Last Updated**: January 16, 2026  
**Project**: Movie Booking System  
**Status**: ✅ Deployed and Running
