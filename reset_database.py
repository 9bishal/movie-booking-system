"""
Script to reset the entire database - clears all data
WARNING: This will permanently delete ALL data from the database
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection
from accounts.models import UserProfile

def reset_database():
    """
    Reset the entire database by deleting all users and profiles
    """
    try:
        print("\n" + "="*60)
        print("🗑️  DATABASE RESET - WARNING!")
        print("="*60)
        print("This will delete ALL users and profiles")
        print("="*60)
        
        # Confirmation
        confirmation = input("\nAre you sure you want to RESET the database? (yes/no): ").strip().lower()
        
        if confirmation != 'yes':
            print("❌ Operation cancelled.")
            return
        
        # Get counts before deletion
        user_count = User.objects.count()
        profile_count = UserProfile.objects.count()
        
        print(f"\nDeleting {user_count} users...")
        print(f"Deleting {profile_count} profiles...")
        
        # Delete all UserProfiles first (due to foreign key relationship)
        UserProfile.objects.all().delete()
        print(f"✅ Deleted {profile_count} user profiles")
        
        # Delete all Users
        User.objects.all().delete()
        print(f"✅ Deleted {user_count} users")
        
        # Verify deletion
        remaining_users = User.objects.count()
        remaining_profiles = UserProfile.objects.count()
        
        print("\n" + "="*60)
        print("✅ Database reset successful!")
        print(f"Remaining users: {remaining_users}")
        print(f"Remaining profiles: {remaining_profiles}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}\n")

if __name__ == '__main__':
    reset_database()
