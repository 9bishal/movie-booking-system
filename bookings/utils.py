import json
import time
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q

# ==============================================================================
# 🧠 CONCEPT: HOW CACHING WORKS IN OUR APP
# Imagine a Movie Theater:
# 1. The DATABASE is the "Main Ledger" (Permanent record, slow to update).
# 2. The CACHE (Redis) is the "Quick-Check Clipboard" (Super fast, temporary).
#
# When a user looks for seats:
# - We check the "Clipboard" first (Cache).
# - If not there, we go to the "Main Ledger" (DB), copy to Clipboard, then show.
# - This prevents crashing the DB when 1,000 people check seats at once.
# ==============================================================================

class SeatManager:
    """Handles logic for showing, reserving, and booking seats using Cache."""
    
    @staticmethod
    def generate_seat_layout(rows=10, cols=12):
        """STEP 0: Create a blank seat map if one doesn't exist."""
        layout = []
        for row in range(rows):
            row_letter = chr(65 + row)  # A, B, C...
            row_seats = []
            for col in range(1, cols + 1):
                # 7th column is a walkway (gap between seats)
                if col == 7:
                    row_seats.append(None)
                else:
                    seat_number = col if col < 7 else col - 1
                    row_seats.append({
                        'seat_id': f"{row_letter}{seat_number}",
                        'row': row_letter,
                        'number': seat_number,
                        'available': True,
                        'type': 'standard',
                        'price': 200.00,
                    })
            layout.append(row_seats)
        return layout
    
    @staticmethod
    def get_seat_layout(showtime_id):
        """STEP 1: Get the full map (layout) for this showtime."""
        # 🕵️ WHY: Performance. Generating the layout every time is wasteful.
        # HOW: We use a showtime-specific key to keep movie maps separate.
        # WHEN: Triggers whenever a user opens the seat selection page.
        cache_key = f"seat_layout_{showtime_id}"
        
        # ❓ "cache.get" tries to find it on our super-fast "Clipboard" (Redis)
        layout = cache.get(cache_key)
        
        if not layout:
            # 🔄 HOW: Fallback. If the cache is empty, we rebuild the map and save it back.
            layout = SeatManager.generate_seat_layout()
            cache.set(cache_key, layout, timeout=3600)  # Keep for 1 hour
        
        return layout
    
    @staticmethod
    def get_available_seats(showtime_id):
        """STEP 2: Get only the seats that are NOT yet booked."""
        # 🕵️ WHY: Accuracy. We need to know which seats are actually for sale.
        # HOW: We combine layout data with existing 'CONFIRMED' bookings from the DB.
        # WHEN: Triggers before showing the seat map and during the 'reserve' validation.
        cache_key = f"available_seats_{showtime_id}"
        available_seats = cache.get(cache_key)
        
        if available_seats is None:
            # 🔄 HOW: Rebuild. If cache is empty, start with the full layout.
            layout = SeatManager.get_seat_layout(showtime_id)
            available_seats = []
            for row in layout:
                for seat in row:
                    if seat and seat['available']:
                        available_seats.append(seat['seat_id'])
            
            # 🕵️ DATABASE CHECK: 
            # WHY: The Database is the final truth. 
            # We must remove seats that have already been SOLD (CONFIRMED).
            from .models import Booking
            from django.utils import timezone
            
            booked_seats_query = Booking.objects.filter(
                showtime_id=showtime_id,
                status='CONFIRMED'
            ).only('seats').values_list('seats', flat=True)
            
            for seats_list in booked_seats_query:
                # 🔄 HOW: Removal. We subtract every sold seat from the 'for-sale' list.
                for seat_id in seats_list:
                    if seat_id in available_seats:
                        available_seats.remove(seat_id)
            
            # �️ CRITICAL: Also check PENDING bookings to prevent race conditions
            # WHY: PENDING bookings are "payment in progress" - seats should be locked
            # HOW: Only consider PENDING bookings that haven't expired yet
            pending_seats_query = Booking.objects.filter(
                showtime_id=showtime_id,
                status='PENDING',
                expires_at__gt=timezone.now()  # Not expired yet
            ).only('seats').values_list('seats', flat=True)
            
            for seats_list in pending_seats_query:
                for seat_id in seats_list:
                    if seat_id in available_seats:
                        available_seats.remove(seat_id)
            
            # 💾 CRITICAL: Use SHORT cache timeout (30 seconds)
            # WHY: Allows seats to become available quickly after Redis TTL expires
            # or when user force-closes tab without triggering ondismiss
            cache.set(cache_key, available_seats, timeout=30)
        
        return available_seats
    
    @staticmethod
    def get_reserved_seats(showtime_id):
        """STEP 3: Get seats that are "In Progress" (User is paying)."""
        # These are seats that aren't booked yet, but someone is trying to.
        cache_key = f"reserved_seats_{showtime_id}"
        redis_reserved = cache.get(cache_key) or []
        
        # 🛡️ CRITICAL: Also include seats from PENDING bookings in DB
        # WHY: Redis cache might expire before booking is confirmed/cancelled
        # This ensures seats in payment flow are always shown as reserved (yellow)
        from .models import Booking
        from django.utils import timezone
        
        # Use expires_at field which is set when booking is created
        # Only include PENDING bookings that haven't expired yet
        # IMPORTANT: Exclude FAILED, CANCELLED, EXPIRED bookings (they should not block seats)
        # OPTIMIZED: Use .only() to fetch only seats field (lighter query)
        pending_bookings = Booking.objects.filter(
            showtime_id=showtime_id,
            status='PENDING',
            expires_at__gt=timezone.now()  # Not expired yet
        ).only('seats').values_list('seats', flat=True)
        
        db_reserved = []
        for seats_list in pending_bookings:
            db_reserved.extend(seats_list)
        
        # Combine Redis and DB reserved seats (no duplicates)
        all_reserved = list(set(redis_reserved + db_reserved))
        return all_reserved
    
    @staticmethod
    def reserve_seats(showtime_id, seat_ids, user_id):
        """STEP 4: Temporarily 'Lock' seats for a user (10-minute timer)."""
        # 🛡️ WHY: Concurrency Protection.
        # This prevents two users from paying for the same seats simultaneously.
        # HOW: We create a 'reservation' key in Redis. Redis handles atomic checks.
        # WHEN: Triggers when the user clicks 'Confirm' or 'Proceed to Payment'.
        if not seat_ids:
            return False
        
        # 🕵️ THE SECURITY CHECK: Are the seats actually free right now?
        available_seats = SeatManager.get_available_seats(showtime_id)
        reserved_seats = SeatManager.get_reserved_seats(showtime_id)
        
        # 🕵️ WHY: Re-entrancy. 
        # Check if the CURRENT user already held these seats (so they don't 'steal' from themselves).
        user_reservation_key = f"seat_reservation_{showtime_id}_{user_id}"
        existing_user_res = cache.get(user_reservation_key)
        my_seats = existing_user_res.get('seat_ids', []) if existing_user_res else []
        
        for seat_id in seat_ids:
            # 🔄 HOW: Collision Detection. 
            # A seat is 'Taken' if it's not available OR someone else has reserved it.
            if seat_id not in available_seats or (seat_id in reserved_seats and seat_id not in my_seats):
                return False
        
        # 🔒 LOCKING THE SEATS:
        # 1. Update the global 'reserved' pool for this showtime.
        # WHY: Visibility. All other users will now see these seats as 'locked'.
        new_reserved = list(set(reserved_seats + seat_ids))
        cache_key = f"reserved_seats_{showtime_id}"
        cache.set(cache_key, new_reserved, timeout=settings.SEAT_RESERVATION_TIMEOUT)
        
        # 2. Record this user's specific lock.
        # WHY: Reconciliation. We need to know WHICH user locked WHICH seats.
        cache.set(user_reservation_key, {
            'seat_ids': seat_ids,
            'reserved_at': time.time()
        }, timeout=settings.SEAT_RESERVATION_TIMEOUT)
        
        return True
    
    @staticmethod
    def release_seats(showtime_id, seat_ids=None, user_id=None):
        """RESCUE: Someone closed the tab or payment failed? Free the seats!"""
        cache_key = f"reserved_seats_{showtime_id}"
        reserved_seats = cache.get(cache_key) or []
        
        # Always clear the user's specific reservation key if user_id is provided
        if user_id:
            reservation_key = f"seat_reservation_{showtime_id}_{user_id}"
            cache.delete(reservation_key)
        
        # Free the specified seats from the global reserved list
        if seat_ids:
            for sid in seat_ids:
                if sid in reserved_seats: 
                    reserved_seats.remove(sid)
        
        # Save the updated list back to cache
        cache.set(cache_key, reserved_seats, timeout=settings.SEAT_RESERVATION_TIMEOUT)
        return True
    
    @staticmethod
    def confirm_seats(showtime_id, seat_ids):
        """FINISH: Payment success! Mark these as GONE from available list."""
        # 1. Remove the temporary 'Lock'
        SeatManager.release_seats(showtime_id, seat_ids)
        
        # 2. Permanently remove from the 'Available' list on our "Clipboard"
        # 🔐 CRITICAL BUG FIX: Don't update cache if it doesn't exist
        # WHY: If cache expired or doesn't exist, we should rebuild from DB instead
        # of saving an empty list which would mark ALL seats as booked!
        # HOW: Only update the cache if it exists in memory
        cache_key = f"available_seats_{showtime_id}"
        available_seats = cache.get(cache_key)
        
        # Only update the cache if it was previously set (exists in Redis/Cache)
        # If cache is None/missing, let get_available_seats() rebuild it from DB on next call
        if available_seats is not None:
            # Cache exists, update it by removing the confirmed seats
            for sid in seat_ids:
                if sid in available_seats: 
                    available_seats.remove(sid)
            # Save the updated 'Available' list so others see these seats as taken
            cache.set(cache_key, available_seats, timeout=3600)
        # else: Cache doesn't exist, skip update. It will be rebuilt from DB on next call
        
        return True

    @staticmethod
    def is_seat_still_available_for_user(showtime_id, seat_ids, user_id):
        """
        🕵️ THE ULTIMATE SAFETY CHECK:
        WHY: Data Authority. Client-side clocks (Razorpay modal) can stay open 
        longer than our server-side safety lock. This is the master check.
        HOW: We re-query the database for any 'CONFIRMED' tickets that might 
        have been issued during the small gap between Redis expiry and Payment success.
        WHEN: Triggers after Razorpay signals success but before we commit the ticket.
        """
        # 1. 🕵️ WHY: Double-check the Database. 
        # Redis is just a 'hint', the SQL database is the 'Law'.
        from .models import Booking
        confirmed_bookings = Booking.objects.filter(
            showtime_id=showtime_id,
            status='CONFIRMED'
        ).exclude(user_id=user_id) # Don't check against the user's own current booking attempt
        
        # 🔄 HOW: Check for Overlap.
        # Since SQLite JSONField doesn't support complex 'contains' queries in the ORM,
        # we iterate through confirmed seat lists to see if our requested seats are present.
        for booking in confirmed_bookings:
            for seat in seat_ids:
                if seat in booking.seats:
                    # 🚨 COLLISION: The seat was sold to someone else in the last 12 minutes!
                    return False
            
        # 🟢 ALL CLEAR: No confirmed booking exists for these seats in this showtime.
        # This means even if Redis lock expired, the seats haven't been bought by anyone else yet.
        return True



class PriceCalculator:
    """
    🧮 WHY THIS EXISTS:
    Calculating money is sensitive. We centralize it here so its consistent 
    across the website.
    """
    # 💡 BEGINNER TIP: Why use 'Decimal' instead of 'float'?
    # Floats (like 0.1) are imprecise in computers. Decimals are exactly like 
    # paper-and-pen math. NEVER use floats for money!
    TAX_RATE = Decimal('0.18')  # 18% GST
    CONVENIENCE_FEE = Decimal('30.00')
    
    @staticmethod
    def calculate_booking_amount(showtime, seat_count, seat_type='standard'):
        """
        💸 HOW: Math Logic
        WHY: Consistency. We centralize pricing here to avoid bugs in multiple places.
        HOW: Base Price + Fees + Taxes. Uses Decimal for precision.
        WHEN: Triggers on the Summary page and when creating the FINAL booking record.
        """
        base_price = showtime.price * seat_count
        
        # 🔄 HOW: Dynamic Multipliers.
        # We increase the price based on seat category (Premium = 1.5x).
        if seat_type == 'premium':
            base_price *= Decimal('1.5')
        elif seat_type == 'sofa':
            base_price *= Decimal('2.0')
        
        # 🏦 HOW: Addons. 
        # Convenience fee covers the platform cost, Taxes (GST) are government mandated.
        convenience_fee = PriceCalculator.CONVENIENCE_FEE
        tax_amount = (base_price + convenience_fee) * PriceCalculator.TAX_RATE
        total_amount = base_price + convenience_fee + tax_amount
        
        return {
            'base_price': round(base_price, 2),
            'convenience_fee': convenience_fee,
            'tax_amount': round(tax_amount, 2),
            'total_amount': round(total_amount, 2),
        }
