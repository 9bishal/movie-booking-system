#!/usr/bin/env python
"""
Quick script to clear all seat caches and show current booking status
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.core.cache import cache
from bookings.models import Booking, Showtime
from bookings.utils import SeatManager
from django.utils import timezone

print("\n" + "="*70)
print("🔧 SEAT BOOKING DIAGNOSTIC & CACHE CLEAR")
print("="*70)

# Clear all caches
print("\n1️⃣ Clearing all seat-related caches...")
showtimes = Showtime.objects.all()
for st in showtimes:
    for key_prefix in ['available_seats', 'reserved_seats', 'seat_layout']:
        cache.delete(f'{key_prefix}_{st.id}')
print(f"   ✅ Cleared cache for {showtimes.count()} showtimes")

# Show booking status
print("\n2️⃣ Current Booking Status:")
print("-"*70)

for st in showtimes[:5]:  # Show first 5
    print(f"\n📽️  {st.movie.title} - {st.get_formatted_time()}")
    print(f"   Showtime ID: {st.id}")
    
    # Count bookings
    confirmed = Booking.objects.filter(showtime=st, status='CONFIRMED')
    pending = Booking.objects.filter(showtime=st, status='PENDING', expires_at__gt=timezone.now())
    
    confirmed_seats = sum(len(b.seats) for b in confirmed)
    pending_seats = sum(len(b.seats) for b in pending)
    
    print(f"   ✅ CONFIRMED: {confirmed.count()} bookings ({confirmed_seats} seats)")
    print(f"   ⏳ PENDING: {pending.count()} bookings ({pending_seats} seats)")
    
    # Show actual seats if any
    if confirmed.exists():
        all_seats = []
        for b in confirmed:
            all_seats.extend(b.seats)
        print(f"   🪑 Booked seats: {', '.join(sorted(all_seats)[:10])}{'...' if len(all_seats) > 10 else ''}")
    
    # Show available count
    available = SeatManager.get_available_seats(st.id)
    layout = SeatManager.get_seat_layout(st.id)
    total = sum(1 for row in layout for seat in row if seat)
    
    print(f"   📊 {len(available)}/{total} seats available")

print("\n" + "="*70)
print("✅ DONE! Now refresh your browser page.")
print("="*70 + "\n")
