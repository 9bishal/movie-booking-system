#!/usr/bin/env python
"""
Delete all users (except superusers)
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def delete_all_users():
    print("👤 Deleting all users...")
    
    total = User.objects.count()
    superusers = User.objects.filter(is_superuser=True).count()
    regular = total - superusers
    
    print(f"📊 Found {total} users ({superusers} superusers, {regular} regular)")
    
    # Delete non-superusers only
    deleted, _ = User.objects.filter(is_superuser=False).delete()
    print(f"✅ Deleted {deleted} regular users!")
    print(f"🛡️  Kept {superusers} superuser(s)")

def delete_all_including_superusers():
    print("👤 Deleting ALL users including superusers...")
    deleted, _ = User.objects.all().delete()
    print(f"✅ Deleted {deleted} users!")

if __name__ == '__main__':
    print("Options:")
    print("1. Delete regular users only (keep superusers)")
    print("2. Delete ALL users (including superusers)")
    choice = input("Enter choice (1 or 2): ")
    
    if choice == '1':
        confirm = input("⚠️  Delete all regular users? Type 'yes': ")
        if confirm.lower() == 'yes':
            delete_all_users()
        else:
            print("❌ Cancelled.")
    elif choice == '2':
        confirm = input("⚠️  Delete ALL users including superusers? Type 'yes': ")
        if confirm.lower() == 'yes':
            delete_all_including_superusers()
        else:
            print("❌ Cancelled.")
    else:
        print("❌ Invalid choice.")
