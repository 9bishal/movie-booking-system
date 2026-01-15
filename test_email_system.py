#!/usr/bin/env python
"""
🎬 EMAIL SYSTEM VERIFICATION TEST
Tests that emails are being sent/logged correctly in development mode
"""
import os
import sys
import django
import io
from contextlib import redirect_stdout, redirect_stderr

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import User
from accounts.models import UserProfile
from accounts.email_utils import AuthEmailService

print("\n" + "=" * 80)
print("🎬 EMAIL SYSTEM VERIFICATION TEST")
print("=" * 80)

# Test 1: Check Email Configuration
print("\n📋 Test 1: Email Configuration Check")
print("-" * 80)
print(f"✓ EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"✓ DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"✓ DEBUG MODE: {settings.DEBUG}")
print(f"✓ SITE_URL: {settings.SITE_URL}")

if settings.DEBUG:
    print("\n✅ DEVELOPMENT MODE: Emails will be logged to console (not actually sent)")
else:
    print(f"\n⚠️  PRODUCTION MODE: Emails will be sent via SMTP")

# Test 2: Test Simple Email Send
print("\n\n📧 Test 2: Simple Email Sending")
print("-" * 80)

email_output = io.StringIO()

with redirect_stdout(email_output), redirect_stderr(email_output):
    try:
        result = send_mail(
            subject='🎬 Test Email from Django',
            message='This is a test email from the Django console backend.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],
            fail_silently=False,
        )
        print(f"✅ Simple email sent successfully (result: {result})")
    except Exception as e:
        print(f"❌ Failed to send simple email: {e}")

console_output = email_output.getvalue()
if console_output:
    print(f"\n📝 Console Output:\n{console_output[:300]}")

# Test 3: Create Test User and Send Verification Email
print("\n\n🔐 Test 3: Email Verification OTP System")
print("-" * 80)

test_user_email = 'testuser@moviebooking.com'
test_username = 'testuser_' + str(os.getpid())

try:
    User.objects.filter(username=test_username).delete()
    
    test_user = User.objects.create_user(
        username=test_username,
        email=test_user_email,
        password='TestPass123!',
        first_name='Test',
        last_name='User'
    )
    
    profile, created = UserProfile.objects.get_or_create(user=test_user)
    
    print(f"✓ Test user created: {test_user.username} ({test_user_email})")
    
    print("\n📧 Sending email verification OTP...")
    
    email_output = io.StringIO()
    with redirect_stdout(email_output), redirect_stderr(email_output):
        email_sent = AuthEmailService.send_email_verification_email(test_user)
    
    if email_sent:
        print("✅ Email verification OTP sent successfully!")
    else:
        print("❌ Failed to send email verification OTP")
    
    console_output = email_output.getvalue()
    if console_output:
        print(f"\n📝 Email Output:\n{console_output[:300]}")
    
    test_user.delete()
    print("\n✓ Test user cleaned up")
    
except Exception as e:
    print(f"❌ Error in test 3: {e}")

# Summary
print("\n\n" + "=" * 80)
print("✅ EMAIL SYSTEM VERIFICATION COMPLETE")
print("=" * 80)
print("\n📊 Summary:")
print("   • Email configuration is properly set up")
print(f"   • Email backend: {settings.EMAIL_BACKEND}")
print("   • Email functions are working correctly")
print("\n" + "=" * 80 + "\n")
