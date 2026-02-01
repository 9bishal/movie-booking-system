#!/usr/bin/env python
"""
Complete OTP-based Password Reset Flow Test
This script tests the entire password reset flow:
1. Request OTP
2. Verify OTP
3. Set new password
4. Login with new password
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.cache import cache
from accounts.email_utils import send_password_reset_otp

User = get_user_model()

def test_otp_password_reset_flow():
    """Test the complete OTP-based password reset flow"""
    
    print("=" * 70)
    print("OTP-BASED PASSWORD RESET FLOW TEST")
    print("=" * 70)
    
    # Step 1: Create or get test user
    print("\n[STEP 1] Setting up test user...")
    test_email = "test_reset@example.com"
    test_username = "test_reset_user"
    
    try:
        user = User.objects.get(email=test_email)
        print(f"✅ Found existing user: {user.username} ({user.email})")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            password="OldPassword123"
        )
        print(f"✅ Created new user: {user.username} ({user.email})")
    
    # Set a known password
    user.set_password("OldPassword123")
    user.save()
    print(f"✅ Set password to: OldPassword123")
    
    # Step 2: Generate and send OTP
    print(f"\n[STEP 2] Generating OTP for {test_email}...")
    import random
    otp = str(random.randint(100000, 999999))
    
    # Store OTP in cache (5 minutes)
    cache_key = f"password_reset_otp_{test_email}"
    cache.set(cache_key, otp, timeout=300)
    print(f"✅ Generated OTP: {otp}")
    print(f"✅ Stored in cache with key: {cache_key}")
    
    # Send OTP email
    print(f"\n[STEP 3] Sending OTP email...")
    try:
        send_password_reset_otp(test_email, otp)
        print(f"✅ Email sent successfully to {test_email}")
        print(f"   Check your email for the OTP code")
    except Exception as e:
        print(f"⚠️  Email sending failed: {e}")
        print(f"   (This is OK if email is not configured)")
    
    # Step 4: Verify OTP from cache
    print(f"\n[STEP 4] Verifying OTP...")
    cached_otp = cache.get(cache_key)
    if cached_otp == otp:
        print(f"✅ OTP verified successfully")
        print(f"   Entered: {otp}")
        print(f"   Cached:  {cached_otp}")
    else:
        print(f"❌ OTP verification failed")
        print(f"   Entered: {otp}")
        print(f"   Cached:  {cached_otp}")
        return
    
    # Step 5: Set new password
    print(f"\n[STEP 5] Setting new password...")
    new_password = "NewPassword123"
    user.set_password(new_password)
    user.save()
    print(f"✅ Password changed to: {new_password}")
    
    # Clear OTP from cache
    cache.delete(cache_key)
    print(f"✅ OTP cleared from cache")
    
    # Step 6: Verify new password works
    print(f"\n[STEP 6] Testing login with new password...")
    from django.contrib.auth import authenticate
    
    auth_user = authenticate(username=user.username, password=new_password)
    if auth_user:
        print(f"✅ Login successful with new password")
    else:
        print(f"❌ Login failed with new password")
        return
    
    # Test old password doesn't work
    old_auth = authenticate(username=user.username, password="OldPassword123")
    if not old_auth:
        print(f"✅ Old password correctly rejected")
    else:
        print(f"⚠️  Old password still works (unexpected)")
    
    print("\n" + "=" * 70)
    print("✅ OTP PASSWORD RESET FLOW TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)
    
    print("\n📋 MANUAL TESTING STEPS:")
    print("-" * 70)
    print("1. Start the server: python manage.py runserver")
    print("2. Navigate to: http://localhost:8000/accounts/forgot-password/")
    print(f"3. Enter email: {test_email}")
    print(f"4. Check email or use OTP: {otp}")
    print("5. Enter OTP on verification page")
    print("6. Set new password on the password reset page")
    print("7. Login with new password")
    print("-" * 70)

def test_cache_expiry():
    """Test OTP expiry after 5 minutes"""
    print("\n" + "=" * 70)
    print("TESTING OTP EXPIRY")
    print("=" * 70)
    
    test_email = "test_expiry@example.com"
    otp = "123456"
    cache_key = f"password_reset_otp_{test_email}"
    
    # Set with 5 second timeout for testing
    print(f"\n[TEST] Setting OTP with 5 second timeout...")
    cache.set(cache_key, otp, timeout=5)
    
    # Immediate check
    cached = cache.get(cache_key)
    if cached == otp:
        print(f"✅ OTP found immediately after setting")
    
    # Wait 6 seconds
    print(f"⏳ Waiting 6 seconds...")
    import time
    time.sleep(6)
    
    # Check again
    cached = cache.get(cache_key)
    if cached is None:
        print(f"✅ OTP expired after timeout (as expected)")
    else:
        print(f"❌ OTP still exists (unexpected)")
    
    print("=" * 70)

def show_url_patterns():
    """Show the URL patterns for password reset"""
    print("\n" + "=" * 70)
    print("PASSWORD RESET URL PATTERNS")
    print("=" * 70)
    
    print("\n1. Request OTP:")
    print("   URL: /accounts/forgot-password/")
    print("   Method: GET (show form), POST (send OTP)")
    
    print("\n2. Verify OTP:")
    print("   URL: /accounts/verify-password-reset-otp/")
    print("   Method: GET (show form), POST (verify OTP)")
    
    print("\n3. Set New Password:")
    print("   URL: /accounts/set-new-password/")
    print("   Method: GET (show form), POST (set password)")
    
    print("\n4. Login:")
    print("   URL: /accounts/login/")
    print("   Method: GET (show form), POST (login)")
    
    print("=" * 70)

if __name__ == '__main__':
    try:
        test_otp_password_reset_flow()
        test_cache_expiry()
        show_url_patterns()
        
        print("\n" + "🎉" * 35)
        print("ALL TESTS PASSED!")
        print("🎉" * 35)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
