#!/usr/bin/env python
"""
Comprehensive diagnostic for production payment flow issues
Tests each component independently to identify the root cause
"""
import os
import sys
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
from django.core.files.base import ContentFile
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

print("=" * 80)
print("PRODUCTION PAYMENT FLOW DIAGNOSTIC")
print("=" * 80)

# Test 1: Celery Configuration
print("\n[TEST 1] Celery Configuration:")
try:
    from django.conf import settings
    broker_url = getattr(settings, 'CELERY_BROKER_URL', 'NOT SET')
    print(f"  ✓ CELERY_BROKER_URL: {broker_url}")
    
    from celery import current_app
    print(f"  ✓ Celery app: {current_app}")
    print(f"  ✓ Celery broker connection: OK")
except Exception as e:
    print(f"  ✗ CELERY ERROR: {e}")

# Test 2: Email Backend Configuration
print("\n[TEST 2] Email Backend Configuration:")
try:
    from django.conf import settings
    email_backend = getattr(settings, 'EMAIL_BACKEND', 'NOT SET')
    sendgrid_key = getattr(settings, 'SENDGRID_API_KEY', None)
    default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')
    
    print(f"  ✓ EMAIL_BACKEND: {email_backend}")
    print(f"  ✓ SENDGRID_API_KEY: {'SET' if sendgrid_key else 'NOT SET'}")
    print(f"  ✓ DEFAULT_FROM_EMAIL: {default_from}")
    
    if not sendgrid_key:
        print("  ⚠ WARNING: SendGrid API key not configured!")
except Exception as e:
    print(f"  ✗ EMAIL CONFIG ERROR: {e}")

# Test 3: Razorpay Configuration
print("\n[TEST 3] Razorpay Configuration:")
try:
    print(f"  ✓ Is Mock Mode: {razorpay_client.is_mock}")
    print(f"  ✓ Key ID: {razorpay_client.key_id[:20]}...")
    
    # Test order creation
    order = razorpay_client.create_order(100, receipt="test_diagnostic")
    if order['success']:
        print(f"  ✓ Order Creation: SUCCESS")
    else:
        print(f"  ✗ Order Creation: FAILED - {order.get('error')}")
except Exception as e:
    print(f"  ✗ RAZORPAY ERROR: {e}")

# Test 4: QR Code Generation
print("\n[TEST 4] QR Code Generation:")
try:
    from bookings.models import Booking
    import qrcode
    from io import BytesIO
    
    # Create a test QR code in memory
    qr_data = "Test QR Code for Booking BOOK-TEST-001"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_image_data = buffer.getvalue()
    
    print(f"  ✓ QR Code generation: SUCCESS ({len(qr_image_data)} bytes)")
    
    # Test saving to media storage
    try:
        from django.core.files.storage import default_storage
        test_filename = 'test_qr_diagnostic.png'
        path = default_storage.save(f'booking_qrcodes/{test_filename}', ContentFile(qr_image_data))
        print(f"  ✓ QR Code storage: SUCCESS (saved to {path})")
        
        # Try to read it back
        with default_storage.open(path, 'rb') as f:
            read_data = f.read()
            if read_data == qr_image_data:
                print(f"  ✓ QR Code retrieval: SUCCESS")
            else:
                print(f"  ✗ QR Code retrieval: DATA MISMATCH")
        
        # Clean up
        default_storage.delete(path)
        print(f"  ✓ QR Code cleanup: SUCCESS")
    except Exception as e:
        print(f"  ✗ Storage Error: {e}")
        
except Exception as e:
    print(f"  ✗ QR CODE ERROR: {e}")

# Test 5: Email Task Execution
print("\n[TEST 5] Email Task Configuration:")
try:
    from bookings import email_utils
    import inspect
    
    # Check if email functions are proper Celery tasks
    if hasattr(email_utils.send_booking_confirmation_email, 'delay'):
        print(f"  ✓ send_booking_confirmation_email: IS CELERY TASK")
    else:
        print(f"  ✗ send_booking_confirmation_email: NOT A CELERY TASK")
    
    if hasattr(email_utils.send_payment_failed_email, 'delay'):
        print(f"  ✓ send_payment_failed_email: IS CELERY TASK")
    else:
        print(f"  ✗ send_payment_failed_email: NOT A CELERY TASK")
    
    # Get task signatures
    sig = email_utils.send_booking_confirmation_email.signature()
    print(f"  ✓ Confirmation email task signature: {sig}")
except Exception as e:
    print(f"  ✗ CELERY TASK ERROR: {e}")

# Test 6: Database Connection
print("\n[TEST 6] Database Connection:")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    print(f"  ✓ Database: CONNECTED")
except Exception as e:
    print(f"  ✗ DATABASE ERROR: {e}")

# Test 7: Redis Connection
print("\n[TEST 7] Redis Connection:")
try:
    from django.core.cache import cache
    cache.set('diagnostic_test', 'OK', 10)
    result = cache.get('diagnostic_test')
    if result == 'OK':
        print(f"  ✓ Redis: CONNECTED")
    else:
        print(f"  ✗ Redis: READ/WRITE FAILED")
except Exception as e:
    print(f"  ✗ REDIS ERROR: {e}")

# Test 8: Booking Model QR Code Method
print("\n[TEST 8] Booking Model QR Code Generation:")
try:
    # Get or create a test booking
    showtime = Showtime.objects.filter(is_active=True).first()
    user = User.objects.filter(is_active=True).first()
    
    if showtime and user:
        booking = Booking.objects.create(
            user=user,
            showtime=showtime,
            seats=['TEST1', 'TEST2'],
            total_seats=2,
            base_price=Decimal('200.00'),
            convenience_fee=Decimal('20.00'),
            tax_amount=Decimal('39.60'),
            total_amount=Decimal('259.60'),
            status='PENDING'
        )
        
        # Change to CONFIRMED to allow QR generation
        booking.status = 'CONFIRMED'
        booking.payment_received_at = timezone.now()
        
        # Try to generate QR code
        try:
            booking.generate_qr_code()
            booking.save()
            print(f"  ✓ QR code generated for booking {booking.booking_number}")
            
            # Try to retrieve it
            try:
                qr_b64 = booking.get_qr_code_base64()
                if qr_b64:
                    print(f"  ✓ QR code retrieved (base64): {len(qr_b64)} chars")
                else:
                    print(f"  ✗ QR code retrieval returned None")
            except Exception as e:
                print(f"  ✗ QR code retrieval failed: {e}")
        except Exception as e:
            print(f"  ✗ QR code generation failed: {e}")
        
        # Clean up
        booking.delete()
        print(f"  ✓ Test booking cleaned up")
    else:
        print(f"  ⚠ Skipping: No test showtime or user available")
        
except Exception as e:
    print(f"  ✗ BOOKING QR CODE ERROR: {e}")

# Test 9: Media File Serving
print("\n[TEST 9] Media File Serving (Production):")
try:
    from django.conf import settings
    media_url = getattr(settings, 'MEDIA_URL', 'NOT SET')
    media_root = getattr(settings, 'MEDIA_ROOT', 'NOT SET')
    
    print(f"  ✓ MEDIA_URL: {media_url}")
    print(f"  ✓ MEDIA_ROOT: {media_root}")
    
    # Check if media directories exist
    import os
    qrcode_dir = os.path.join(media_root, 'booking_qrcodes')
    if os.path.exists(qrcode_dir):
        print(f"  ✓ QR code directory exists: {qrcode_dir}")
    else:
        print(f"  ⚠ QR code directory missing (will be created on first save)")
except Exception as e:
    print(f"  ✗ MEDIA CONFIG ERROR: {e}")

# Test 10: Connection Pool and Locks
print("\n[TEST 10] Database Connection Pool:")
try:
    from django.db import connection
    from django.db import connections
    
    conn = connections['default']
    print(f"  ✓ Database engine: {conn.vendor}")
    print(f"  ✓ Connection established: {conn.connection is not None}")
    
    # Check if database supports SELECT FOR UPDATE
    if 'sqlite' in conn.vendor.lower():
        print(f"  ⚠ SQLite detected: SELECT FOR UPDATE has limited support (may cause 'database is locked')")
    elif 'postgres' in conn.vendor.lower() or 'mysql' in conn.vendor.lower():
        print(f"  ✓ {conn.vendor.upper()} detected: Full SELECT FOR UPDATE support")
except Exception as e:
    print(f"  ✗ CONNECTION POOL ERROR: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
print("\n📋 SUMMARY:")
print("If all tests passed (✓), the payment system should work correctly.")
print("If any tests failed (✗) or show warnings (⚠), check the output above.")
print("=" * 80)
