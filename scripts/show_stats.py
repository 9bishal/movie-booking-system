#!/usr/bin/env python
"""
Show database statistics
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from bookings.models import Booking
from movies.models import Movie
from movies.theater_models import Theater, Screen, Showtime

User = get_user_model()

def show_stats():
    print("=" * 50)
    print("📊 DATABASE STATISTICS")
    print("=" * 50)
    
    # Users
    users = User.objects.count()
    superusers = User.objects.filter(is_superuser=True).count()
    print(f"\n👤 Users: {users} (superusers: {superusers})")
    
    # Movies
    movies = Movie.objects.count()
    print(f"🎬 Movies: {movies}")
    
    # Theaters
    theaters = Theater.objects.count()
    screens = Screen.objects.count()
    print(f"🏛️  Theaters: {theaters}")
    print(f"📺 Screens: {screens}")
    
    # Showtimes
    showtimes = Showtime.objects.count()
    active = Showtime.objects.filter(is_active=True).count()
    future = Showtime.objects.filter(date__gte=timezone.now().date()).count()
    print(f"🕐 Showtimes: {showtimes} (active: {active}, future: {future})")
    
    # Bookings
    total_bookings = Booking.objects.count()
    confirmed = Booking.objects.filter(status='CONFIRMED').count()
    pending = Booking.objects.filter(status='PENDING').count()
    failed = Booking.objects.filter(status='FAILED').count()
    cancelled = Booking.objects.filter(status='CANCELLED').count()
    
    print(f"\n🎫 Bookings: {total_bookings}")
    print(f"   ✅ Confirmed: {confirmed}")
    print(f"   ⏳ Pending: {pending}")
    print(f"   ❌ Failed: {failed}")
    print(f"   🚫 Cancelled: {cancelled}")
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    show_stats()
