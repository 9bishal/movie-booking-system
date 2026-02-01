# 🚀 Quick Start: SendGrid Setup

**⏱️ Estimated Time**: 15 minutes

---

## 1️⃣ Create SendGrid Account (3 min)
1. Go to https://sendgrid.com/
2. Sign up (free tier: 100 emails/day forever)
3. Verify your email

---

## 2️⃣ Verify Sender Email (5 min)
1. **Login to SendGrid Dashboard**
2. **Navigate**: Settings → Sender Authentication → Single Sender Verification
3. **Click**: "Create New Sender"
4. **Fill Form**:
   - From Name: `Movie Booking System`
   - From Email: `your-email@gmail.com` (or your domain)
   - Reply To: Same or support email
   - Company details (can be personal)
5. **Check Email**: Click verification link
6. **Copy** verified email for later

---

## 3️⃣ Create API Key (2 min)
1. **Navigate**: Settings → API Keys
2. **Click**: "Create API Key"
3. **Name**: `Movie Booking Production`
4. **Permissions**: Restricted Access
   - ✅ Turn ON **Mail Send** → Full Access
   - ❌ Everything else OFF
5. **Click**: "Create & View"
6. **⚠️ COPY API KEY IMMEDIATELY** (you won't see it again!)
   - Format: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## 4️⃣ Local Testing (Optional - 3 min)
```bash
# Create .env file
cp .env.example .env

# Edit .env and add:
SENDGRID_API_KEY=SG.your_actual_key_here
DEFAULT_FROM_EMAIL=your-verified-email@gmail.com

# Test
python test_sendgrid_email.py your-email@example.com

# Should see: ✅ Email sent successfully!
```

---

## 5️⃣ Commit & Push (2 min)
```bash
git add .
git commit -m "Migrate to SendGrid email backend"
git push origin main
```

---

## 6️⃣ Deploy to Render (5 min)

### Option A: Dashboard (Recommended)
1. Go to https://dashboard.render.com/
2. Click **New** → **Blueprint**
3. Connect your GitHub repository
4. Wait for automatic deployment (~3-5 min)
5. Go to web service → **Environment** tab
6. Find `SENDGRID_API_KEY` → Click **Edit**
7. Paste your API key → **Save Changes**
8. Also set `DEFAULT_FROM_EMAIL` to your verified sender email
9. Service redeploys automatically

### Option B: CLI
```bash
# Set environment variables
render env set SENDGRID_API_KEY "SG.your_key_here" --service movie-booking-system
render env set DEFAULT_FROM_EMAIL "your-verified-email@gmail.com" --service movie-booking-system

# Deploy
render deploy --service movie-booking-system
```

---

## 7️⃣ Test in Production (3 min)
1. **Open your deployed app**: `https://movie-booking-system.onrender.com`
2. **Register** a new test account
3. **Check email** for activation link
4. **Test password reset** (Forgot Password)
5. **Verify** emails arrive successfully

### Check SendGrid Dashboard:
- Activity → See all sent emails
- Stats → Delivery rates
- If issues → Troubleshoot section

---

## 🎯 Key Values to Copy

```bash
# From SendGrid:
SENDGRID_API_KEY=SG.________________________________
DEFAULT_FROM_EMAIL=your-verified-email@example.com

# To set in Render environment variables
```

---

## ✅ Success Checklist

- [ ] SendGrid account created ✓
- [ ] Sender email verified ✓
- [ ] API key created (starts with `SG.`) ✓
- [ ] API key copied and saved securely ✓
- [ ] Local test passed (optional) ✓
- [ ] Code pushed to GitHub ✓
- [ ] Render Blueprint deployed ✓
- [ ] `SENDGRID_API_KEY` set in Render ✓
- [ ] `DEFAULT_FROM_EMAIL` set in Render ✓
- [ ] Production email test successful ✓

---

## 🐛 Quick Troubleshooting

### "Invalid API Key"
- Double-check key starts with `SG.`
- Ensure no extra spaces when copying
- Recreate key if needed

### "Sender email not verified"
- Check SendGrid dashboard: Settings → Sender Authentication
- `DEFAULT_FROM_EMAIL` must match verified sender
- Click verification link in email

### "Emails not arriving"
- Check spam folder
- Check SendGrid Activity tab for bounce reason
- Ensure `SENDGRID_API_KEY` is set in Render environment
- Check Render logs: `render logs --service movie-booking-system --tail`

---

## 📚 Full Documentation

For detailed information, see:
- **SENDGRID_MIGRATION_GUIDE.md** - Complete setup guide
- **SENDGRID_MIGRATION_SUMMARY.md** - Technical changes
- **test_sendgrid_email.py** - Test script

---

## 🆘 Need Help?

- SendGrid Docs: https://docs.sendgrid.com/
- Django-Anymail Docs: https://anymail.dev/
- Render Docs: https://render.com/docs/

---

**Last Updated**: December 2024
**Status**: ✅ Ready to Deploy
