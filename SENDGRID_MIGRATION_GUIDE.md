# SendGrid Migration Guide

## Overview
This project has been migrated from **MailerSend** to **SendGrid** for email delivery. This guide covers all the changes made and how to set up SendGrid for your deployment.

---

## 🔄 Changes Made

### 1. **Django Settings** (`moviebooking/settings.py`)
- **Changed**: Email backend from `anymail.backends.mailersend.EmailBackend` to `anymail.backends.sendgrid.EmailBackend`
- **Changed**: Environment variable from `MAILERSEND_API_KEY` to `SENDGRID_API_KEY`
- **Changed**: ANYMAIL configuration from `MAILERSEND_API_TOKEN` to `SENDGRID_API_KEY`

**Before:**
```python
MAILERSEND_API_KEY = os.environ.get('MAILERSEND_API_KEY', '')
if MAILERSEND_API_KEY:
    EMAIL_BACKEND = 'anymail.backends.mailersend.EmailBackend'
    ANYMAIL = {
        'MAILERSEND_API_TOKEN': MAILERSEND_API_KEY,
    }
```

**After:**
```python
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
if SENDGRID_API_KEY:
    EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'
    ANYMAIL = {
        'SENDGRID_API_KEY': SENDGRID_API_KEY,
    }
```

### 2. **Environment Variables** (`.env.example`)
- **Changed**: `MAILERSEND_API_KEY` → `SENDGRID_API_KEY`
- **Updated**: Comments to reference SendGrid instead of MailerSend

### 3. **Render Deployment** (`render.yaml`)
- **Changed**: Environment variable from `MAILERSEND_API_KEY` to `SENDGRID_API_KEY`

### 4. **Dependencies** (`requirements.txt`)
- **No changes needed**: `django-anymail==10.2` already supports SendGrid

---

## 🚀 SendGrid Setup Guide

### Step 1: Create SendGrid Account
1. Go to [SendGrid](https://sendgrid.com/)
2. Sign up for a free account (includes 100 emails/day forever)
3. Verify your email address

### Step 2: Verify Sender Identity
SendGrid requires you to verify your sender identity before sending emails.

**Option A: Single Sender Verification (Quick Start)**
1. Go to **Settings** > **Sender Authentication** > **Single Sender Verification**
2. Click **Create New Sender**
3. Fill in your details:
   - From Name: `Movie Booking System`
   - From Email Address: `noreply@yourdomain.com` (use a real email you control)
   - Reply To: Your support email
4. Check your email and verify the sender
5. Use this email as your `DEFAULT_FROM_EMAIL`

**Option B: Domain Authentication (Recommended for Production)**
1. Go to **Settings** > **Sender Authentication** > **Authenticate Your Domain**
2. Follow the wizard to add DNS records to your domain
3. Once verified, you can send from any email address on that domain

### Step 3: Create API Key
1. Go to **Settings** > **API Keys**
2. Click **Create API Key**
3. Name: `Movie Booking System Production`
4. Permissions: Select **Restricted Access**
   - Turn on **Mail Send** (Full Access)
5. Click **Create & View**
6. **IMPORTANT**: Copy the API key immediately (you won't see it again!)
7. Store it securely - you'll need it for deployment

---

## 🔧 Local Development Setup

### 1. Update Your `.env` File
```bash
# Copy .env.example to .env if you haven't already
cp .env.example .env

# Edit .env and add your SendGrid API key
SENDGRID_API_KEY=SG.your_actual_api_key_here
DEFAULT_FROM_EMAIL=noreply@yourdomain.com  # Use your verified sender
```

### 2. Test Email Sending
Create a test script `test_sendgrid.py`:

```python
from django.core.mail import send_mail
from django.conf import settings

# Send a test email
send_mail(
    subject='Test Email from Movie Booking System',
    message='This is a test email sent using SendGrid.',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['your-email@example.com'],  # Replace with your email
    fail_silently=False,
)
print("✅ Email sent successfully!")
```

Run the test:
```bash
python manage.py shell < test_sendgrid.py
```

Check your inbox for the test email.

---

## 🌐 Render Deployment Setup

### Method 1: Using Render Dashboard (Recommended)

1. **Deploy Using Blueprint**
   - Push your code to GitHub
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click **New** > **Blueprint**
   - Connect your repository
   - Render will detect `render.yaml` and set up all services

2. **Set SendGrid API Key**
   - After deployment, go to your web service
   - Click **Environment** tab
   - Find `SENDGRID_API_KEY` (it will show as "Not Set")
   - Click **Edit** and paste your SendGrid API key
   - Click **Save Changes**
   - Service will redeploy automatically

3. **Update DEFAULT_FROM_EMAIL (Optional)**
   - If you want to use a different sender email
   - Edit `DEFAULT_FROM_EMAIL` in the Environment tab
   - Use the email you verified in SendGrid

### Method 2: Using Render CLI

```bash
# Set the SendGrid API key
render env set SENDGRID_API_KEY "SG.your_actual_api_key_here" --service movie-booking-system

# Set the from email (if different from default)
render env set DEFAULT_FROM_EMAIL "noreply@yourdomain.com" --service movie-booking-system

# Redeploy to apply changes
render deploy --service movie-booking-system
```

---

## 📧 Email Features in the System

Your movie booking system sends emails for:

1. **Account Activation** - New user registration
2. **Password Reset** - When users forget their password
3. **Booking Confirmation** - After successful payment
4. **Payment Failed** - When payment fails
5. **Late Payment Reminder** - Automated reminders via Celery tasks

All these emails will now be sent through SendGrid.

---

## 🧪 Testing Email in Production

After deploying to Render:

1. **Test User Registration**
   - Register a new user account
   - Check if activation email is received
   - Verify the email contains correct links with your production URL

2. **Test Password Reset**
   - Click "Forgot Password"
   - Check if reset email is received

3. **Test Booking Confirmation**
   - Complete a test booking
   - Check if confirmation email is received

4. **Check SendGrid Dashboard**
   - Go to SendGrid **Activity** tab
   - You'll see all sent emails, delivery status, and analytics

---

## 📊 SendGrid vs MailerSend Comparison

| Feature | SendGrid | MailerSend |
|---------|----------|------------|
| Free Tier | 100 emails/day forever | 3,000/month (12,000 first month) |
| Setup Complexity | Medium | Easy |
| Deliverability | Excellent (industry leader) | Good |
| Analytics | Comprehensive | Basic |
| Templates | Rich template editor | Basic templates |
| API Stability | Very stable | Newer service |

---

## 🔒 Security Best Practices

1. **Never commit API keys to Git**
   - API keys are in `.env` (already in `.gitignore`)
   - `.env.example` only shows format, not real keys

2. **Use Restricted API Keys**
   - Only grant "Mail Send" permission
   - Don't use "Full Access" keys

3. **Rotate Keys Periodically**
   - Create new API keys every 3-6 months
   - Delete old keys after rotation

4. **Monitor Usage**
   - Check SendGrid dashboard regularly
   - Set up alerts for quota limits

---

## 🐛 Troubleshooting

### Emails Not Sending
1. **Check API Key**
   ```bash
   # On Render, check environment variable
   render env list --service movie-booking-system | grep SENDGRID
   ```

2. **Check Sender Verification**
   - Ensure your `DEFAULT_FROM_EMAIL` is verified in SendGrid
   - Check SendGrid **Activity** tab for bounce/block reasons

3. **Check Logs**
   ```bash
   # View Render logs
   render logs --service movie-booking-system --tail
   ```

### Common Errors

**Error: "Invalid API Key"**
- Solution: Double-check your API key is correct
- Make sure it starts with `SG.`

**Error: "Sender email not verified"**
- Solution: Go to SendGrid and verify your sender email
- Update `DEFAULT_FROM_EMAIL` to match verified sender

**Error: "Emails stuck in console backend"**
- Solution: Make sure `SENDGRID_API_KEY` environment variable is set
- Check Django logs for warning messages

---

## 📝 Checklist for Migration

- [ ] SendGrid account created and verified
- [ ] Sender email verified in SendGrid
- [ ] SendGrid API key created with "Mail Send" permission
- [ ] `.env` file updated with `SENDGRID_API_KEY`
- [ ] Local email test successful
- [ ] Code pushed to GitHub
- [ ] Render deployment successful
- [ ] `SENDGRID_API_KEY` set in Render environment
- [ ] Production email test successful (registration/password reset)
- [ ] SendGrid Activity dashboard shows successful deliveries

---

## 🆘 Support

### SendGrid Support
- [SendGrid Documentation](https://docs.sendgrid.com/)
- [SendGrid Support](https://support.sendgrid.com/)
- [API Reference](https://docs.sendgrid.com/api-reference)

### Django-Anymail Support
- [Django-Anymail Docs](https://anymail.dev/)
- [SendGrid Backend Configuration](https://anymail.dev/en/stable/esps/sendgrid/)

### Project-Specific Help
- Check `EMAIL_INVESTIGATION_SUMMARY.md` for email system architecture
- Review Django logs for detailed error messages
- Test with `python manage.py shell` for debugging

---

## 🎉 Benefits of This Migration

1. **Better Free Tier**: 100 emails/day forever (vs 3,000/month)
2. **Industry Standard**: SendGrid is the most widely used email service
3. **Better Analytics**: Comprehensive delivery and engagement tracking
4. **Proven Reliability**: Used by millions of applications worldwide
5. **Excellent Documentation**: Extensive guides and support resources

---

**Last Updated**: December 2024
**Version**: 1.0
**Status**: ✅ Migration Complete
