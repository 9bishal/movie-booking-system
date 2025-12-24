"""
❓ WHY THIS FILE EXISTS:
This is a custom 'Diagnostic' command. It helps developers quickly check 
if their local environment (.env) is correctly configured for Redis, Razorpay, and Email.
"""
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Setup payment configuration and test email'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎬 MovieBooking Payment Setup'))
        self.stdout.write('=' * 50)
        
        # Check Razorpay configuration
        if getattr(settings, 'RAZORPAY_KEY_ID', None) and getattr(settings, 'RAZORPAY_KEY_SECRET', None):
            self.stdout.write(self.style.SUCCESS('✓ Razorpay configured'))
            self.stdout.write(f'   Key ID: {settings.RAZORPAY_KEY_ID[:10]}...')
        else:
            self.stdout.write(self.style.WARNING('⚠ Razorpay not configured'))
            self.stdout.write('   Get test credentials from: https://razorpay.com/docs/')
            self.stdout.write('   Add to .env file:')
            self.stdout.write('   RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx')
            self.stdout.write('   RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx')
        
        # Check Email configuration
        if getattr(settings, 'EMAIL_HOST_USER', None) and getattr(settings, 'EMAIL_HOST_PASSWORD', None):
            self.stdout.write(self.style.SUCCESS('✓ Email configured'))
            self.stdout.write(f'   From: {settings.DEFAULT_FROM_EMAIL}')
        else:
            self.stdout.write(self.style.WARNING('⚠ Email not configured'))
            self.stdout.write('   For Gmail:')
            self.stdout.write('   1. Enable 2FA on Google account')
            self.stdout.write('   2. Generate App Password')
            self.stdout.write('   3. Add to .env file:')
            self.stdout.write('   EMAIL_HOST_USER=your-email@gmail.com')
            self.stdout.write('   EMAIL_HOST_PASSWORD=your-app-password')
        
        # Check Redis
        try:
            import redis
            # Use REDIS_URL from settings or default
            redis_url = getattr(settings, 'REDIS_URL', 'redis://127.0.0.1:6379/1')
            r = redis.Redis.from_url(redis_url)
            r.ping()
            self.stdout.write(self.style.SUCCESS('✓ Redis connected'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Redis not connected: {str(e)}'))
            self.stdout.write('   Install and start Redis:')
            self.stdout.write('   Windows: Download from redis.io')
            self.stdout.write('   Mac: brew install redis && brew services start redis')
            self.stdout.write('   Linux: sudo apt install redis-server')
        
        self.stdout.write('=' * 50)
        self.stdout.write(self.style.SUCCESS('Setup complete!'))