"""
Script to delete all users from the database
WARNING: This will permanently delete all User and UserProfile records
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile

def delete_all_users():
    """
    Delete all users and their profiles from the database
    Handles foreign key constraints by deleting related data first
    """
    try:
        # Get counts before deletion
        user_count = User.objects.count()
        profile_count = UserProfile.objects.count()
        
        print("\n" + "="*60)
        print("🗑️  DELETE ALL USERS - WARNING!")
        print("="*60)
        print(f"Users to be deleted: {user_count}")
        print(f"Profiles to be deleted: {profile_count}")
        print("="*60)
        
        # Confirmation
        confirmation = input("\nAre you sure you want to delete ALL users? (yes/no): ").strip().lower()
        
        if confirmation != 'yes':
            print("❌ Operation cancelled.")
            return
        
        print("\n🗑️  Starting deletion process...")
        
        # Step 1: Delete all related data first
        deleted_counts = {}
        
        # Delete bookings
        try:
            from bookings.models import Booking
            count = Booking.objects.count()
            Booking.objects.all().delete()
            deleted_counts['bookings'] = count
        except Exception as e:
            print(f"⚠️  Warning: Could not delete bookings: {e}")
        
        # Delete any reviews if they exist
        try:
            from django.apps import apps
            if apps.is_installed('reviews'):
                Review = apps.get_model('reviews', 'Review')
                count = Review.objects.count()
                Review.objects.all().delete()
                deleted_counts['reviews'] = count
        except:
            pass  # Reviews app might not exist or be installed
        
        # Delete user sessions
        try:
            from django.contrib.sessions.models import Session
            count = Session.objects.count()
            Session.objects.all().delete()
            deleted_counts['sessions'] = count
        except Exception as e:
            print(f"⚠️  Warning: Could not delete sessions: {e}")
        
        # Clear Django admin log entries
        try:
            from django.contrib.admin.models import LogEntry
            count = LogEntry.objects.count()
            LogEntry.objects.all().delete()
            deleted_counts['log_entries'] = count
        except Exception as e:
            print(f"⚠️  Warning: Could not delete log entries: {e}")
        
        # Step 2: Delete user profiles
        try:
            UserProfile.objects.all().delete()
            deleted_counts['user_profiles'] = profile_count
        except Exception as e:
            print(f"⚠️  Warning: Could not delete all profiles: {e}")
        
        # Step 3: Use raw SQL to delete users if needed (bypass Django ORM constraints)
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                # First, get list of users
                users = list(User.objects.values_list('id', 'username'))
                
                # Try Django ORM first
                deleted_via_orm = 0
                remaining_users = []
                
                for user_id, username in users:
                    try:
                        User.objects.filter(id=user_id).delete()
                        deleted_via_orm += 1
                    except Exception:
                        remaining_users.append((user_id, username))
                
                # If some users couldn't be deleted via ORM, try raw SQL
                if remaining_users:
                    print(f"⚠️  {len(remaining_users)} users have foreign key constraints, using raw SQL...")
                    
                    # Disable foreign key checks (SQLite specific)
                    cursor.execute("PRAGMA foreign_keys=OFF;")
                    
                    deleted_via_sql = 0
                    for user_id, username in remaining_users:
                        try:
                            cursor.execute("DELETE FROM auth_user WHERE id = ?", [user_id])
                            deleted_via_sql += 1
                            print(f"   Deleted user: {username}")
                        except Exception as e:
                            print(f"   Failed to delete {username}: {e}")
                    
                    # Re-enable foreign key checks
                    cursor.execute("PRAGMA foreign_keys=ON;")
                    
                    deleted_counts['users_via_sql'] = deleted_via_sql
                
                deleted_counts['users_via_orm'] = deleted_via_orm
                
        except Exception as e:
            print(f"❌ Error during user deletion: {e}")
        
        # Print deletion summary
        print("\n📊 Deletion Summary:")
        for item, count in deleted_counts.items():
            if count > 0:
                print(f"   {item}: {count}")
        
        # Final counts
        remaining_users = User.objects.count()
        remaining_profiles = UserProfile.objects.count()
        
        print("\n" + "="*60)
        if remaining_users == 0 and remaining_profiles == 0:
            print("✅ ALL USERS AND PROFILES DELETED SUCCESSFULLY!")
        else:
            print(f"⚠️  DELETION COMPLETED WITH REMAINING RECORDS")
            print(f"   Remaining users: {remaining_users}")
            print(f"   Remaining profiles: {remaining_profiles}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}\n")

if __name__ == '__main__':
    delete_all_users()


