#!/usr/bin/env python
"""
Reset entire database (delete all data)
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.core.cache import cache
from django.contrib.auth import get_user_model
from bookings.models import Booking
from movies.models import Movie
from movies.theater_models import Theater

User = get_user_model()

def reset_database():
    print("🗑️  Resetting entire database...")
    
    # Delete in order to avoid FK issues
    print("\n1️⃣ Deleting bookings...")
    count, _ = Booking.objects.all().delete()
    print(f"   Deleted {count} bookings")
    
    print("\n2️⃣ Deleting theaters (and screens, showtimes)...")
    count, _ = Theater.objects.all().delete()
    print(f"   Deleted {count} theaters")
    
    print("\n3️⃣ Deleting movies...")
    count, _ = Movie.objects.all().delete()
    print(f"   Deleted {count} movies")
    
    print("\n4️⃣ Deleting regular users...")
    count, _ = User.objects.filter(is_superuser=False).delete()
    print(f"   Deleted {count} users")
    
    print("\n5️⃣ Clearing cache...")
    cache.clear()
    print("   Cache cleared!")
    
    print("\n✅ Database reset complete!")
    print(f"🛡️  Kept {User.objects.filter(is_superuser=True).count()} superuser(s)")

if __name__ == '__main__':
    print("=" * 50)
    print("⚠️  WARNING: This will delete ALL data!")
    print("=" * 50)
    confirm = input("Type 'RESET' to confirm: ")
    if confirm == 'RESET':
        reset_database()
    else:
        print("❌ Cancelled.")
