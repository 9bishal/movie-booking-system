#!/usr/bin/env python
"""
Release all booked/reserved seats (cancel all bookings)
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from bookings.models import Booking
from django.core.cache import cache

def release_all_seats():
    print("🪑 Releasing all booked seats...")
    
    # Count bookings
    total = Booking.objects.count()
    confirmed = Booking.objects.filter(status='CONFIRMED').count()
    pending = Booking.objects.filter(status='PENDING').count()
    
    print(f"📊 Found {total} bookings ({confirmed} confirmed, {pending} pending)")
    
    # Delete all bookings
    Booking.objects.all().delete()
    print("✅ All bookings deleted!")
    
    # Clear cache
    cache.clear()
    print("✅ Cache cleared!")

if __name__ == '__main__':
    confirm = input("⚠️  This will DELETE ALL bookings. Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        release_all_seats()
    else:
        print("❌ Cancelled.")
