#!/usr/bin/env python
"""
Test SMTP connection to Gmail on Railway.
This script explicitly tests if we can connect to Gmail's SMTP server.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.core.mail import get_connection, EmailMessage
from django.conf import settings
import smtplib
import ssl

def test_smtp_connection():
    """Test SMTP connection and send a test email."""
    print("=" * 60)
    print("📧 SMTP CONNECTION TEST")
    print("=" * 60)
    
    # Print current email settings
    print("\n📋 Current Email Settings:")
    print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"   EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
    print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"   EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        print("\n⚠️  Using console backend - emails will only be printed to console")
        print("   Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD to use SMTP")
        return
    
    # Test 1: Raw SMTP connection
    print("\n🔌 Test 1: Raw SMTP Connection")
    try:
        host = settings.EMAIL_HOST
        port = settings.EMAIL_PORT
        
        print(f"   Connecting to {host}:{port}...")
        
        if settings.EMAIL_USE_SSL:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host, port, context=context, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            if settings.EMAIL_USE_TLS:
                server.starttls()
        
        print("   ✅ Connection established!")
        
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            print(f"   Authenticating as {settings.EMAIL_HOST_USER}...")
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            print("   ✅ Authentication successful!")
        
        server.quit()
        print("   ✅ Raw SMTP test passed!")
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Authentication failed: {e}")
        print("\n   💡 Tips:")
        print("   - Make sure 2FA is enabled on your Gmail account")
        print("   - Use an App Password, not your regular Gmail password")
        print("   - Generate at: https://myaccount.google.com/apppasswords")
        return
    except smtplib.SMTPConnectError as e:
        print(f"   ❌ Connection failed: {e}")
        print("   Gmail SMTP may be blocked on this platform")
        return
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        return
    
    # Test 2: Django email sending
    print("\n📤 Test 2: Django Email Sending")
    try:
        # Get a connection with fail_silently=False to see errors
        connection = get_connection(fail_silently=False)
        connection.open()
        print("   ✅ Django email connection opened!")
        
        # Send test email
        test_email = settings.EMAIL_HOST_USER or 'test@example.com'
        email = EmailMessage(
            subject='🧪 SMTP Test from Railway',
            body='This is a test email sent from Railway to verify SMTP connectivity.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[test_email],
            connection=connection
        )
        
        print(f"   Sending test email to {test_email}...")
        result = email.send(fail_silently=False)
        
        if result:
            print("   ✅ Email sent successfully!")
            print(f"   📬 Check inbox of {test_email}")
        else:
            print("   ❌ Email sending returned 0")
        
        connection.close()
        
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")

if __name__ == '__main__':
    test_smtp_connection()
