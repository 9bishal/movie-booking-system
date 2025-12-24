import json
import time
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings

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
        # We use a unique ID so different movies don't mix up their seats!
        cache_key = f"seat_layout_{showtime_id}"
        
        # ❓ "cache.get" tries to find it on our super-fast "Clipboard"
        layout = cache.get(cache_key)
        
        if not layout:
            # If not on Clipboard, generate a new map and "set" it on Clipboard
            layout = SeatManager.generate_seat_layout()
            cache.set(cache_key, layout, timeout=3600)  # Keep for 1 hour
        
        return layout
    
    @staticmethod
    def get_available_seats(showtime_id):
        """STEP 2: Get only the seats that are NOT yet booked."""
        cache_key = f"available_seats_{showtime_id}"
        available_seats = cache.get(cache_key)
        
        if available_seats is None:
            # Start by assuming all seats in the layout are free
            layout = SeatManager.get_seat_layout(showtime_id)
            available_seats = []
            for row in layout:
                for seat in row:
                    if seat and seat['available']:
                        available_seats.append(seat['seat_id'])
            # Save this list to cache
            cache.set(cache_key, available_seats, timeout=3600)
        
        return available_seats
    
    @staticmethod
    def get_reserved_seats(showtime_id):
        """STEP 3: Get seats that are "In Progress" (User is paying)."""
        # These are seats that aren't booked yet, but someone is trying to.
        cache_key = f"reserved_seats_{showtime_id}"
        return cache.get(cache_key) or []
    
    @staticmethod
    def reserve_seats(showtime_id, seat_ids, user_id):
        """STEP 4: Temporarily 'Lock' seats for a user (10-minute timer)."""
        if not seat_ids:
            return False
        
        # 🛡️ THE SECURITY CHECK:
        # Are the seats actually free? Are they not already held by someone else?
        available_seats = SeatManager.get_available_seats(showtime_id)
        reserved_seats = SeatManager.get_reserved_seats(showtime_id)
        
        for seat_id in seat_ids:
            if seat_id not in available_seats or seat_id in reserved_seats:
                # If even ONE seat is taken, the whole request fails!
                return False
        
        # 🔒 LOCKING THE SEATS:
        # We add them to the 'reserved' list in the cache.
        reserved_seats.extend(seat_ids)
        cache_key = f"reserved_seats_{showtime_id}"
        # SEAT_RESERVATION_TIMEOUT is usually 10 mins (set in settings.py)
        cache.set(cache_key, reserved_seats, timeout=settings.SEAT_RESERVATION_TIMEOUT)
        
        # Record WHICH user tried to book, so we can release it later if they fail.
        reservation_key = f"seat_reservation_{showtime_id}_{user_id}"
        cache.set(reservation_key, {
            'seat_ids': seat_ids,
            'reserved_at': time.time()
        }, timeout=settings.SEAT_RESERVATION_TIMEOUT)
        
        return True
    
    @staticmethod
    def release_seats(showtime_id, seat_ids=None, user_id=None):
        """RESCUE: Someone closed the tab or payment failed? Free the seats!"""
        cache_key = f"reserved_seats_{showtime_id}"
        reserved_seats = cache.get(cache_key) or []
        
        if seat_ids:
            # Free specific seats
            for sid in seat_ids:
                if sid in reserved_seats: reserved_seats.remove(sid)
        elif user_id:
            # Free all seats this user was trying to buy
            reservation_key = f"seat_reservation_{showtime_id}_{user_id}"
            user_res = cache.get(reservation_key)
            if user_res:
                for sid in user_res.get('seat_ids', []):
                    if sid in reserved_seats: reserved_seats.remove(sid)
                cache.delete(reservation_key)
        
        # Save the updated list back to cache
        cache.set(cache_key, reserved_seats, timeout=settings.SEAT_RESERVATION_TIMEOUT)
        return True
    
    @staticmethod
    def confirm_seats(showtime_id, seat_ids):
        """FINISH: Payment success! Mark these as GONE from available list."""
        # 1. Remove the temporary 'Lock'
        SeatManager.release_seats(showtime_id, seat_ids)
        
        # 2. Permanently remove from the 'Available' list on our "Clipboard"
        cache_key = f"available_seats_{showtime_id}"
        available_seats = cache.get(cache_key) or []
        for sid in seat_ids:
            if sid in available_seats: available_seats.remove(sid)
        
        # Save the updated 'Available' list so others see these seats as taken
        cache.set(cache_key, available_seats, timeout=3600)
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
        1. Multiply seats by price.
        2. Add a static convenience fee.
        3. Calculate 18% tax on the result.
        """
        base_price = showtime.price * seat_count
        
        # Apply seat type multiplier
        if seat_type == 'premium':
            base_price *= Decimal('1.5')
        elif seat_type == 'sofa':
            base_price *= Decimal('2.0')
        
        convenience_fee = PriceCalculator.CONVENIENCE_FEE
        tax_amount = (base_price + convenience_fee) * PriceCalculator.TAX_RATE
        total_amount = base_price + convenience_fee + tax_amount
        
        return {
            'base_price': round(base_price, 2),
            'convenience_fee': convenience_fee,
            'tax_amount': round(tax_amount, 2),
            'total_amount': round(total_amount, 2),
        }