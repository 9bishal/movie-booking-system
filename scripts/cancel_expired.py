#!/usr/bin/env python
"""
Cancel expired pending bookings
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from bookings.models import Booking
from django.utils import timezone
from django.core.cache import cache

def cancel_expired():
    print("⏰ Cancelling expired pending bookings...")
    
    now = timezone.now()
    expired = Booking.objects.filter(
        status='PENDING',
        expires_at__lt=now
    )
    
    count = expired.count()
    print(f"📊 Found {count} expired pending bookings")
    
    if count > 0:
        expired.update(status='EXPIRED')
        print(f"✅ Marked {count} bookings as EXPIRED")
        
        # Clear cache
        cache.clear()
        print("✅ Cache cleared!")
    else:
        print("✅ No expired bookings to cancel")

if __name__ == '__main__':
    cancel_expired()
