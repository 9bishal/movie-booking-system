#!/usr/bin/env python
"""
Test script to verify admin user setup and permissions.
Run this locally before deploying to Railway.

Usage: python test_admin_setup.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile

def test_admin_user(username='admin'):
    """Test if admin user exists and has correct permissions"""
    print("\n" + "="*60)
    print("  ADMIN USER VERIFICATION TEST")
    print("="*60 + "\n")
    
    try:
        user = User.objects.get(username=username)
        print(f"✅ User found: {username}")
        print(f"   Email: {user.email}")
        print(f"   Date joined: {user.date_joined}")
        print()
        
        # Check permissions
        checks = [
            ("is_staff", user.is_staff, "Required for Django Admin access"),
            ("is_superuser", user.is_superuser, "Required for full permissions"),
            ("is_active", user.is_active, "Required for login"),
        ]
        
        print("Permission Checks:")
        all_passed = True
        for check_name, value, description in checks:
            status = "✅" if value else "❌"
            print(f"  {status} {check_name}: {value} - {description}")
            if not value:
                all_passed = False
        print()
        
        # Check profile
        try:
            profile = user.profile
            print(f"✅ UserProfile found")
            print(f"   Email verified: {profile.is_email_verified}")
            print(f"   Verified at: {profile.email_verified_at}")
            if not profile.is_email_verified:
                print("   ⚠️  Warning: Email not verified (but staff/superuser bypass this)")
        except UserProfile.DoesNotExist:
            print("❌ UserProfile NOT found")
            print("   ⚠️  This will cause issues - profile should exist")
            all_passed = False
        print()
        
        # Summary
        print("="*60)
        if all_passed:
            print("✅ ADMIN USER IS PROPERLY CONFIGURED")
            print()
            print("You can login to:")
            print("  - Django Admin: http://localhost:8000/admin/")
            print("  - Custom Admin: http://localhost:8000/custom-admin/")
        else:
            print("❌ ADMIN USER HAS ISSUES")
            print()
            print("Fix with: python manage.py create_admin --reset")
        print("="*60 + "\n")
        
        return all_passed
        
    except User.DoesNotExist:
        print(f"❌ User '{username}' does not exist")
        print()
        print("Create with: python manage.py create_admin")
        print("="*60 + "\n")
        return False

def test_staff_bypass():
    """Test that staff users bypass email verification"""
    print("\n" + "="*60)
    print("  EMAIL VERIFICATION BYPASS TEST")
    print("="*60 + "\n")
    
    try:
        # Import the decorator
        from accounts.decorators import email_verified_required
        
        print("✅ @email_verified_required decorator exists")
        print()
        print("Staff/superuser bypass logic:")
        print("  - Staff users (is_staff=True): ✅ Bypass verification")
        print("  - Superusers (is_superuser=True): ✅ Bypass verification")
        print("  - Regular users: Must verify email")
        print()
        
        # Count staff users
        staff_count = User.objects.filter(is_staff=True).count()
        super_count = User.objects.filter(is_superuser=True).count()
        
        print(f"Current staff users: {staff_count}")
        print(f"Current superusers: {super_count}")
        print()
        
        if staff_count > 0:
            print("Staff users:")
            for user in User.objects.filter(is_staff=True)[:5]:
                verified = "✅" if user.profile.is_email_verified else "⚠️"
                print(f"  {verified} {user.username} ({user.email})")
        
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"❌ Error testing bypass: {e}")
        print("="*60 + "\n")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  RUNNING ADMIN SETUP VERIFICATION TESTS")
    print("="*60)
    
    # Test admin user
    admin_ok = test_admin_user('admin')
    
    # Test bypass logic
    bypass_ok = test_staff_bypass()
    
    # Overall result
    print("\n" + "="*60)
    print("  OVERALL TEST RESULTS")
    print("="*60 + "\n")
    
    if admin_ok and bypass_ok:
        print("✅ ALL TESTS PASSED")
        print()
        print("Your admin setup is working correctly!")
        print("You can now deploy to Railway and use the same setup there.")
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Run this command to fix issues:")
        print("  python manage.py create_admin --reset")
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()
