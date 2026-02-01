# Render Deployment Guide - Movie Booking System

## ✅ Completed Steps

### 1. Fixed Admin Dashboard
- ✅ Updated `dashboard.js` to properly populate movie and theater dropdowns
- ✅ Fixed chart rendering to display real booking data
- ✅ Validated all API endpoints return correct data

### 2. Prepared Deployment Configuration
- ✅ Created `render.yaml` with proper service definitions
- ✅ Created `build.sh` for automated build process
- ✅ Fixed Redis service to include IP allow list (`0.0.0.0/0`)
- ✅ Fixed PostgreSQL configuration in databases section
- ✅ Validated `render.yaml` using Render CLI

### 3. Git Repository
- ✅ Committed all changes to GitHub
- ✅ Pushed to remote repository: https://github.com/9bishal/movie-booking-system.git

## 🚀 Deploy to Render

### Option 1: Deploy via Render Dashboard (Recommended)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com/

2. **Create New Blueprint**
   - Click "New +" button
   - Select "Blueprint"
   - Connect your GitHub repository: `9bishal/movie-booking-system`
   - Render will automatically detect the `render.yaml` file

3. **Review and Apply**
   - Review the plan summary:
     - 1 PostgreSQL Database (movie-booking-db)
     - 1 Redis Cache (movie-booking-redis)
     - 1 Web Service (movie-booking-system)
   - Click "Apply"

4. **Configure Environment Variables**
   After the services are created, add these required environment variables to the web service:
   
   - `RAZORPAY_KEY_ID`: Your Razorpay test/live key ID
   - `RAZORPAY_KEY_SECRET`: Your Razorpay test/live key secret
   - `SENDGRID_API_KEY`: Your SendGrid API key
   - `DEFAULT_FROM_EMAIL`: Your verified sender email (e.g., noreply@yourdomain.com)
   - `SITE_URL`: Update to your actual Render URL (e.g., https://your-app-name.onrender.com)

5. **Wait for Deployment**
   - Render will automatically build and deploy your application
   - The build process will run `build.sh` which:
     - Installs dependencies
     - Collects static files
     - Runs database migrations
     - Creates a superuser if needed

### Option 2: Deploy via Render CLI

If you prefer using the CLI, you can monitor the deployment:

```bash
# Check service status
render services list

# View service logs
render services logs <service-id>
```

## 📝 Deployment Configuration Summary

### Services Created

1. **PostgreSQL Database** (`movie-booking-db`)
   - Plan: Free
   - Region: Oregon
   - Database: moviebooking
   - User: moviebooking

2. **Redis Cache** (`movie-booking-redis`)
   - Plan: Free
   - Region: Oregon
   - Memory Policy: allkeys-lru
   - IP Allow List: 0.0.0.0/0 (all connections)

3. **Web Service** (`movie-booking-system`)
   - Plan: Free
   - Region: Oregon
   - Runtime: Python 3.12.0
   - Build: `./build.sh`
   - Start: `gunicorn moviebooking.wsgi:application`

### Environment Variables

Auto-configured:
- `DATABASE_URL`: Linked to PostgreSQL database
- `REDIS_URL`: Linked to Redis cache
- `SECRET_KEY`: Auto-generated
- `DEBUG`: False
- `PYTHON_VERSION`: 3.12.0
- `ALLOWED_HOSTS`: .onrender.com

Required (manual setup):
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `SENDGRID_API_KEY`
- `DEFAULT_FROM_EMAIL`
- `SITE_URL` (update with actual URL)

## 🔍 Post-Deployment Verification

1. **Check Service Status**
   - Ensure all services are "Live" in the Render dashboard
   - Check build logs for any errors

2. **Access Your Application**
   - Visit your Render URL: https://movie-booking-system.onrender.com
   - Or your custom domain if configured

3. **Test Admin Dashboard**
   - Navigate to: https://your-app.onrender.com/custom-admin/
   - Login with the superuser credentials
   - Verify the dashboard loads correctly
   - Check that movie and theater filters work
   - Confirm charts display real data

4. **Test Core Features**
   - Browse movies
   - View showtimes
   - Test booking flow
   - Verify payment integration (with Razorpay test keys)
   - Check email notifications

## 🛠️ Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Ensure all dependencies in `requirements.txt` are compatible
- Verify `build.sh` has execute permissions

### Database Connection Issues
- Ensure `DATABASE_URL` is properly linked
- Check PostgreSQL service is running
- Review connection logs

### Redis Connection Issues
- Verify `REDIS_URL` is properly linked
- Ensure IP allow list includes your service (0.0.0.0/0)
- Check Redis service status

### Static Files Not Loading
- Ensure `build.sh` runs `python manage.py collectstatic`
- Check `STATIC_ROOT` and `STATIC_URL` settings
- Verify WhiteNoise is configured in `settings.py`

### Admin Dashboard Not Working
- Clear browser cache
- Check that static files are collected
- Verify API endpoints return data: `/custom-admin/api/movies/`, `/custom-admin/api/theaters/`

## 📚 Additional Resources

- Render Documentation: https://render.com/docs
- Render Blueprint Spec: https://render.com/docs/blueprint-spec
- Django Deployment Checklist: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

## ✅ Deployment Checklist

- [x] Fixed admin dashboard filtering and charts
- [x] Created and validated `render.yaml`
- [x] Created `build.sh` with proper build steps
- [x] Fixed Redis IP allow list issue
- [x] Fixed PostgreSQL configuration
- [x] Committed and pushed all changes to GitHub
- [ ] Deploy via Render dashboard
- [ ] Configure required environment variables
- [ ] Verify all services are running
- [ ] Test application functionality
- [ ] Set up custom domain (optional)
- [ ] Configure SSL certificate (auto with Render)
- [ ] Monitor application logs and performance

## 🎉 Success!

Your Movie Booking System is now ready for deployment on Render! Follow the steps above to complete the deployment process.

**Important:** Remember to add your Razorpay and SendGrid credentials in the Render dashboard environment variables section after the initial deployment.

---

**Deployment Date:** $(date)
**Repository:** https://github.com/9bishal/movie-booking-system
**Render Dashboard:** https://dashboard.render.com/
