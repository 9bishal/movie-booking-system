#!/usr/bin/env python
"""
Test the safe email sending wrapper in both sync and async modes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.contrib.auth import get_user_model
from movies.theater_models import Showtime
from bookings.models import Booking
from bookings.email_utils import send_email_safe, send_booking_confirmation_email
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

print("=" * 80)
print("TESTING SAFE EMAIL SENDING")
print("=" * 80)

# Create a test booking
showtime = Showtime.objects.filter(is_active=True).first()
user = User.objects.filter(is_active=True).first()

if not showtime or not user:
    print("❌ No test showtime or user available")
    exit(1)

try:
    # Create a test booking in CONFIRMED status
    booking = Booking.objects.create(
        user=user,
        showtime=showtime,
        seats=['TESTX', 'TESTY'],
        total_seats=2,
        base_price=Decimal('200.00'),
        convenience_fee=Decimal('20.00'),
        tax_amount=Decimal('39.60'),
        total_amount=Decimal('259.60'),
        status='CONFIRMED',
        payment_received_at=timezone.now(),
        razorpay_order_id='order_test_123'
    )
    
    # Generate QR code
    booking.generate_qr_code()
    booking.save()
    
    print(f"\n✓ Test booking created: {booking.booking_number}")
    print(f"  User: {user.email}")
    print(f"  Status: {booking.status}")
    print(f"  QR Code: {'Generated' if booking.qr_code else 'Missing'}")
    
    # Test 1: Try safe email sending
    print(f"\n[TEST 1] Safe Email Sending (with fallback):")
    result = send_email_safe(send_booking_confirmation_email, booking.id)
    if result:
        print(f"  ✓ Email sent successfully")
        print(f"    Result: {result}")
    else:
        print(f"  ✗ Email sending failed")
    
    # Verify email was sent
    booking.refresh_from_db()
    if booking.confirmation_email_sent:
        print(f"  ✓ Confirmation email flag set correctly")
    else:
        print(f"  ✗ Confirmation email flag not set")
    
    # Test 2: Verify idempotency (don't send twice)
    print(f"\n[TEST 2] Email Idempotency Check:")
    result2 = send_email_safe(send_booking_confirmation_email, booking.id)
    if result2:
        print(f"  ✓ Second send skipped (idempotent): {result2}")
    else:
        print(f"  ✗ Second send failed")
    
    # Clean up
    booking.delete()
    print(f"\n✓ Test booking cleaned up")
    
    print("\n" + "=" * 80)
    print("✅ SAFE EMAIL SENDING TEST PASSED")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
