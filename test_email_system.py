#!/usr/bin/env python
"""
Email System Diagnostic & Fix Script
Tests email configuration and sends a test email
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import smtplib

print("=" * 70)
print("📧 EMAIL SYSTEM DIAGNOSTIC")
print("=" * 70)

# Step 1: Check environment variables
print("\n1️⃣ Checking Email Configuration...")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER or '❌ NOT SET'}")
print(f"   EMAIL_HOST_PASSWORD: {'✅ SET' if settings.EMAIL_HOST_PASSWORD else '❌ NOT SET'}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
    print("\n❌ ERROR: Email credentials not configured!")
    print("\nTo fix:")
    print("1. Open .env file")
    print("2. Set EMAIL_HOST_USER=your-email@gmail.com")
    print("3. Set EMAIL_HOST_PASSWORD=your-app-password")
    print("\nNote: Use Gmail App Password, not your regular password")
    print("Get app password: https://myaccount.google.com/apppasswords")
    exit(1)

print("   ✅ Email configuration looks good!")

# Step 2: Check template folder
print("\n2️⃣ Checking Email Templates...")
template_dir = os.path.join(settings.BASE_DIR, 'email_templates')
if os.path.exists(template_dir):
    templates = os.listdir(template_dir)
    print(f"   ✅ Template folder exists: {template_dir}")
    print(f"   Found templates: {', '.join(templates)}")
else:
    print(f"   ❌ Template folder not found: {template_dir}")
    exit(1)

# Step 3: Test SMTP connection
print("\n3️⃣ Testing SMTP Connection...")
try:
    smtp = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
    smtp.set_debuglevel(0)
    smtp.starttls()
    smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    smtp.quit()
    print("   ✅ SMTP connection successful!")
except smtplib.SMTPAuthenticationError as e:
    print(f"   ❌ Authentication failed: {e}")
    print("\n   POSSIBLE FIXES:")
    print("   1. Use Gmail App Password (not regular password)")
    print("   2. Enable 2-Step Verification in Gmail")
    print("   3. Generate App Password: https://myaccount.google.com/apppasswords")
    exit(1)
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    exit(1)

# Step 4: Check Celery configuration
print("\n4️⃣ Checking Celery Configuration...")
try:
    from celery import current_app
    print(f"   ✅ Celery app: {current_app}")
    print(f"   Broker URL: {settings.CELERY_BROKER_URL}")
    print(f"   Result backend: {settings.CELERY_RESULT_BACKEND}")
except Exception as e:
    print(f"   ⚠️  Celery check failed: {e}")

# Step 5: Send test email
print("\n5️⃣ Sending Test Email...")
try:
    # Simple test
    subject = "🎬 Test Email from Movie Booking System"
    message = "If you're seeing this, your email system is working! ✅"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient = settings.EMAIL_HOST_USER  # Send to self
    
    send_mail(
        subject,
        message,
        from_email,
        [recipient],
        fail_silently=False,
    )
    
    print(f"   ✅ Test email sent to {recipient}")
    print(f"   Check your inbox!")
except Exception as e:
    print(f"   ❌ Failed to send test email: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 6: Test with HTML template
print("\n6️⃣ Testing HTML Email with Template...")
try:
    # Create mock context
    context = {
        'user': type('obj', (object,), {
            'username': 'TestUser',
            'email': settings.EMAIL_HOST_USER,
            'get_full_name': lambda: 'Test User'
        })(),
        'booking': type('obj', (object,), {
            'booking_number': 'TEST001',
            'total_amount': 500,
            'get_seats_display': lambda: 'A1, A2'
        })(),
        'movie': type('obj', (object,), {
            'title': 'Test Movie',
        })(),
        'showtime': type('obj', (object,), {
            'date': '2026-01-10',
            'start_time': '18:00',
        })(),
        'theater': type('obj', (object,), {
            'name': 'Test Theater',
        })(),
        'qr_code': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
    }
    
    # Render template
    html_content = render_to_string('booking_confirmation.html', context)
    text_content = render_to_string('booking_confirmation.txt', context)
    
    # Send HTML email
    email = EmailMultiAlternatives(
        '🎬 Test Booking Confirmation',
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [settings.EMAIL_HOST_USER]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
    
    print(f"   ✅ HTML email sent successfully!")
    print(f"   Check your inbox for a formatted email!")
except Exception as e:
    print(f"   ❌ Failed to send HTML email: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 7: Test Celery task (if Celery is running)
print("\n7️⃣ Testing Celery Task...")
try:
    from bookings.email_utils import send_booking_confirmation_email
    
    print("   ℹ️  To test Celery, make sure:")
    print("   1. Redis is running: redis-server")
    print("   2. Celery worker is running: celery -A moviebooking worker -l info")
    print("   3. Create a real booking and complete payment")
    print("   ")
    print("   Celery task registered: ✅")
    print(f"   Task name: {send_booking_confirmation_email.name}")
except Exception as e:
    print(f"   ⚠️  Celery task check failed: {e}")

print("\n" + "=" * 70)
print("✅ EMAIL SYSTEM DIAGNOSTIC COMPLETE!")
print("=" * 70)
print("\n📋 SUMMARY:")
print("   ✅ Email configuration: OK")
print("   ✅ SMTP connection: OK")
print("   ✅ Templates: OK")
print("   ✅ Test email sent: OK")
print("   ✅ HTML email sent: OK")
print("\n🎉 Your email system is working!")
print("\n📧 Check your inbox:", settings.EMAIL_HOST_USER)
print("\n" + "=" * 70)
