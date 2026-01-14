#!/usr/bin/env python
"""
Delete all theaters, screens, and showtimes
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from movies.theater_models import Theater, Screen, Showtime
from django.core.cache import cache

def delete_all_theaters():
    print("🏛️  Deleting all theaters...")
    
    theaters = Theater.objects.count()
    screens = Screen.objects.count()
    showtimes = Showtime.objects.count()
    
    print(f"📊 Found {theaters} theaters, {screens} screens, {showtimes} showtimes")
    
    # Delete theaters (cascades to screens and showtimes)
    deleted, details = Theater.objects.all().delete()
    print(f"✅ Deleted {deleted} items!")
    
    # Clear cache
    cache.clear()
    print("✅ Cache cleared!")

def delete_showtimes_only():
    print("🕐 Deleting all showtimes only...")
    deleted, _ = Showtime.objects.all().delete()
    print(f"✅ Deleted {deleted} showtimes!")
    cache.clear()

if __name__ == '__main__':
    print("Options:")
    print("1. Delete all theaters (includes screens & showtimes)")
    print("2. Delete showtimes only")
    choice = input("Enter choice (1 or 2): ")
    
    if choice == '1':
        confirm = input("⚠️  Delete all theaters? Type 'yes': ")
        if confirm.lower() == 'yes':
            delete_all_theaters()
        else:
            print("❌ Cancelled.")
    elif choice == '2':
        confirm = input("⚠️  Delete all showtimes? Type 'yes': ")
        if confirm.lower() == 'yes':
            delete_showtimes_only()
        else:
            print("❌ Cancelled.")
    else:
        print("❌ Invalid choice.")
