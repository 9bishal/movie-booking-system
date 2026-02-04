#!/usr/bin/env python
"""
Test script to diagnose payment flow issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.contrib.auth import get_user_model
from movies.theater_models import Showtime
from bookings.models import Booking
from bookings.razorpay_utils import razorpay_client
from bookings.utils import SeatManager
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

print("=" * 70)
print("PAYMENT FLOW DIAGNOSTIC TEST")
print("=" * 70)

# 1. Check Razorpay Configuration
print("\n1. Razorpay Configuration:")
print(f"   - Is Mock Mode: {razorpay_client.is_mock}")
print(f"   - Key ID: {razorpay_client.key_id}")
print(f"   - Key Secret: {'*' * 10} (hidden)")

# 2. Test Order Creation
print("\n2. Testing Order Creation:")
order_data = razorpay_client.create_order(
    amount=500,
    receipt="test_diagnostic_123"
)
if order_data['success']:
    print(f"   ✅ Order created successfully!")
    print(f"   - Order ID: {order_data['order_id']}")
    print(f"   - Amount: {order_data['amount']} paise")
else:
    print(f"   ❌ Order creation failed: {order_data.get('error')}")

# 3. Check for active showtimes
print("\n3. Active Showtimes:")
future_showtimes = Showtime.objects.filter(
    date__gte=timezone.now().date(),
    is_active=True
).order_by('date', 'start_time')[:5]

if future_showtimes.exists():
    print(f"   ✅ Found {future_showtimes.count()} active future showtimes")
    for showtime in future_showtimes:
        print(f"   - {showtime.movie.title} | {showtime.date} {showtime.start_time} | {showtime.screen.name}")
else:
    print("   ⚠️ No active future showtimes found")

# 4. Check for test user
print("\n4. Test User:")
test_user = User.objects.filter(is_active=True).first()
if test_user:
    print(f"   ✅ Test user: {test_user.username} ({test_user.email})")
    email_verified = getattr(test_user, 'is_email_verified', 'N/A')
    print(f"   - Email verified: {email_verified}")
else:
    print("   ❌ No active user found")

# 5. Check Redis connectivity
print("\n5. Redis Connectivity:")
try:
    from django.core.cache import cache
    cache.set('test_key', 'test_value', 10)
    result = cache.get('test_key')
    if result == 'test_value':
        print("   ✅ Redis is working correctly")
    else:
        print("   ❌ Redis test failed")
except Exception as e:
    print(f"   ❌ Redis error: {e}")

# 6. Test complete booking flow
print("\n6. Testing Complete Booking Flow:")
if future_showtimes.exists() and test_user:
    showtime = future_showtimes.first()
    
    print(f"   Testing with showtime: {showtime.movie.title} | {showtime.date} {showtime.start_time}")
    
    # Check available seats and pick real ones
    available_seats = SeatManager.get_available_seats(showtime.id)
    print(f"   - Available seats: {len(available_seats)}")
    
    if len(available_seats) >= 2:
        test_seats = available_seats[:2]
        print(f"   - Test seats: {test_seats}")
    
        # Try to reserve seats
        success = SeatManager.reserve_seats(showtime.id, test_seats, test_user.id)
        if success:
            print(f"   ✅ Seats reserved successfully in Redis")
        
            # Try to create a booking
            try:
                booking = Booking.objects.create(
                    user=test_user,
                    showtime=showtime,
                    seats=test_seats,
                    total_seats=len(test_seats),
                    base_price=Decimal('200.00'),
                    convenience_fee=Decimal('20.00'),
                    tax_amount=Decimal('39.60'),
                    total_amount=Decimal('259.60'),
                    status='PENDING'
                )
                print(f"   ✅ Booking created: {booking.booking_number}")
                
                # Try to create Razorpay order
                order_data = razorpay_client.create_order(
                    amount=booking.total_amount,
                    receipt=f"booking_{booking.booking_number}"
                )
                
                if order_data['success']:
                    print(f"   ✅ Razorpay order created: {order_data['order_id']}")
                    booking.razorpay_order_id = order_data['order_id']
                    booking.save()
                    print(f"   ✅ Booking updated with order ID")
                    
                    # Clean up test booking
                    print("\n   Cleaning up test booking...")
                    booking.status = 'CANCELLED'
                    booking.save()
                    SeatManager.release_seats(showtime.id, test_seats, user_id=test_user.id)
                    print(f"   ✅ Test booking cancelled and seats released")
                    
                else:
                    print(f"   ❌ Razorpay order creation failed: {order_data.get('error')}")
                    booking.delete()
                    
            except Exception as e:
                print(f"   ❌ Booking creation failed: {e}")
                SeatManager.release_seats(showtime.id, test_seats, user_id=test_user.id)
        else:
            print(f"   ❌ Seat reservation failed")
    else:
        print("   ⚠️ Not enough available seats for test (need at least 2)")
else:
    print("   ⚠️ Skipping flow test (no showtime or user available)")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
print("\nIf all checks passed, the payment system should work correctly.")
print("Check your browser console for any JavaScript errors.")
print("=" * 70)
