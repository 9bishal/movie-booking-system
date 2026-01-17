"""
Script to create or update a superuser.
This is safe to run multiple times - it creates if missing or updates if exists.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile

# Get credentials from environment or use defaults
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@moviebooking.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

try:
    # Try to get existing user
    user = User.objects.get(username=username)
    print(f"✅ Superuser '{username}' already exists")
    
    # Ensure user is superuser and staff
    if not user.is_superuser or not user.is_staff:
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"   Updated to superuser status")
    
    # Ensure profile exists with verified email
    profile, created = UserProfile.objects.get_or_create(user=user)
    if not profile.is_email_verified:
        profile.is_email_verified = True
        profile.save()
        print(f"   Email verified")
    
except User.DoesNotExist:
    # Create new superuser
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    
    # Create verified profile
    UserProfile.objects.create(user=user, is_email_verified=True)
    
    print(f"✅ Superuser created successfully!")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"\n⚠️  IMPORTANT: Change the password after first login!")
