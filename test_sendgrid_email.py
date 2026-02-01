"""
Test SendGrid Email Configuration
Run this to verify SendGrid is working correctly.

Usage:
    python test_sendgrid_email.py your-email@example.com
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_sendgrid(recipient_email):
    """Test sending email via SendGrid"""
    print("🔍 Checking SendGrid Configuration...")
    print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    sendgrid_key = os.environ.get('SENDGRID_API_KEY', '')
    if sendgrid_key:
        print(f"   SENDGRID_API_KEY: Set (starts with {sendgrid_key[:8]}...)")
    else:
        print("   ⚠️  SENDGRID_API_KEY: Not set (using console backend)")
    
    print("\n📧 Sending test email...")
    
    try:
        send_mail(
            subject='🎬 Test Email from Movie Booking System',
            message='''
This is a test email sent using SendGrid!

If you're receiving this, your SendGrid integration is working correctly.

✅ Email backend: SendGrid
✅ Django-Anymail: Configured
✅ From: {}

---
Movie Booking System
Powered by SendGrid
            '''.format(settings.DEFAULT_FROM_EMAIL),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        print("✅ Email sent successfully!")
        print(f"   Check your inbox at: {recipient_email}")
        print("\n💡 If using SendGrid:")
        print("   - Check SendGrid Activity dashboard for delivery status")
        print("   - Email should arrive within a few seconds")
        print("   - Check spam folder if not in inbox")
        
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        print("\n🔍 Troubleshooting:")
        print("   1. Check if SENDGRID_API_KEY is set in .env")
        print("   2. Verify sender email is verified in SendGrid")
        print("   3. Check SendGrid dashboard for any issues")
        print("   4. Make sure DEFAULT_FROM_EMAIL matches verified sender")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_sendgrid_email.py your-email@example.com")
        sys.exit(1)
    
    recipient = sys.argv[1]
    print("=" * 60)
    print("   SendGrid Email Test")
    print("=" * 60)
    test_sendgrid(recipient)
    print("=" * 60)
