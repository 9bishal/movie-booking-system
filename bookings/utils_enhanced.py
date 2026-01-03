"""
🔧 Enhanced Seat Management with Atomic Operations
WHY: Prevents race conditions and double bookings
WHAT: Redis-based atomic seat locking with proper invalidation
WHEN: Used for all seat reservation operations
"""

import json
import time
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q
from django_redis import get_redis_connection
import logging

logger = logging.getLogger(__name__)

# ==============================================================================
# 🔐 CACHE KEY MANAGEMENT
# Centralized key generation with versioning
# ==============================================================================

class CacheKeyBuilder:
    """Centralized cache key generation with versioning"""
    
    VERSION = "v2"
    PREFIX = "moviebooking"
    
    @staticmethod
    def seat_layout(showtime_id):
        return f"{CacheKeyBuilder.PREFIX}:{CacheKeyBuilder.VERSION}:seat_layout:{showtime_id}"
    
    @staticmethod
    def available_seats(showtime_id):
        return f"{CacheKeyBuilder.PREFIX}:{CacheKeyBuilder.VERSION}:available_seats:{showtime_id}"
    
    @staticmethod
    def reserved_seats(showtime_id):
        return f"{CacheKeyBuilder.PREFIX}:{CacheKeyBuilder.VERSION}:reserved_seats:{showtime_id}"
    
    @staticmethod
    def seat_lock(showtime_id, seat_id):
        return f"{CacheKeyBuilder.PREFIX}:{CacheKeyBuilder.VERSION}:seat_lock:{showtime_id}:{seat_id}"
    
    @staticmethod
    def user_reservation(showtime_id, user_id):
        return f"{CacheKeyBuilder.PREFIX}:{CacheKeyBuilder.VERSION}:user_res:{showtime_id}:{user_id}"


class CacheTimeouts:
    """Centralized timeout management"""
    SEAT_LAYOUT = 3600  # 1 hour (static data)
    AVAILABLE_SEATS = 300  # 5 minutes (dynamic)
    RESERVED_SEATS = 720  # 12 minutes
    SEAT_LOCK = 720  # 12 minutes


class CacheInvalidator:
    """Centralized cache invalidation management"""
    
    @staticmethod
    def invalidate_showtime_cache(showtime_id):
        """Invalidate all cache related to a showtime"""
        try:
            cache_keys = [
                CacheKeyBuilder.seat_layout(showtime_id),
                CacheKeyBuilder.available_seats(showtime_id),
                CacheKeyBuilder.reserved_seats(showtime_id),
            ]
            cache.delete_many(cache_keys)
            logger.info(f"Cache invalidated for showtime {showtime_id}")
        except Exception as e:
            logger.error(f"Cache invalidation error for showtime {showtime_id}: {e}")
    
    @staticmethod
    def invalidate_on_booking_confirmed(booking):
        """Called when booking is confirmed"""
        CacheInvalidator.invalidate_showtime_cache(booking.showtime.id)
        logger.info(f"Cache invalidated for confirmed booking {booking.booking_number}")
    
    @staticmethod
    def invalidate_on_booking_expired(booking):
        """Called when booking expires"""
        CacheInvalidator.invalidate_showtime_cache(booking.showtime.id)
        logger.info(f"Cache invalidated for expired booking {booking.booking_number}")


# ==============================================================================
# 🪑 SEAT MANAGER - ATOMIC OPERATIONS
# ==============================================================================

class SeatManager:
    """
    🔐 Enhanced seat management with atomic operations
    Prevents race conditions using Redis SETNX
    """
    
    @staticmethod
    def generate_seat_layout(rows=10, cols=12):
        """Generate blank seat map"""
        layout = []
        for row in range(rows):
            row_letter = chr(65 + row)  # A, B, C...
            row_seats = []
            for col in range(1, cols + 1):
                if col == 7:
                    row_seats.append(None)  # Walkway
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
        """Get seat layout (cached)"""
        cache_key = CacheKeyBuilder.seat_layout(showtime_id)
        layout = cache.get(cache_key)
        
        if not layout:
            layout = SeatManager.generate_seat_layout()
            cache.set(cache_key, layout, timeout=CacheTimeouts.SEAT_LAYOUT)
            logger.info(f"Seat layout cached for showtime {showtime_id}")
        
        return layout
    
    @staticmethod
    def get_available_seats(showtime_id):
        """
        🔍 Get available seats (optimized caching)
        Cache timeout reduced to 5 minutes for fresher data
        """
        cache_key = CacheKeyBuilder.available_seats(showtime_id)
        available_seats = cache.get(cache_key)
        
        if available_seats is None:
            logger.info(f"Cache MISS: Rebuilding available seats for showtime {showtime_id}")
            
            # Start with full layout
            layout = SeatManager.get_seat_layout(showtime_id)
            available_seats = []
            for row in layout:
                for seat in row:
                    if seat and seat['available']:
                        available_seats.append(seat['seat_id'])
            
            # Remove confirmed bookings from database
            from .models import Booking
            booked_seats_query = Booking.objects.filter(
                showtime_id=showtime_id,
                status='CONFIRMED'
            ).values_list('seats', flat=True)
            
            for seats_list in booked_seats_query:
                for seat_id in seats_list:
                    if seat_id in available_seats:
                        available_seats.remove(seat_id)
            
            # Cache with shorter timeout for dynamic data
            cache.set(cache_key, available_seats, timeout=CacheTimeouts.AVAILABLE_SEATS)
            logger.info(f"Available seats cached: {len(available_seats)} seats for showtime {showtime_id}")
        else:
            logger.info(f"Cache HIT: Available seats for showtime {showtime_id}")
        
        return available_seats
    
    @staticmethod
    def get_reserved_seats(showtime_id):
        """Get currently reserved (locked) seats"""
        cache_key = CacheKeyBuilder.reserved_seats(showtime_id)
        return cache.get(cache_key) or []
    
    @staticmethod
    def lock_seat_atomic(showtime_id, seat_id, user_id, timeout=720):
        """
        🔒 ATOMIC: Lock a single seat using Redis SETNX
        Returns True if lock acquired, False otherwise
        """
        try:
            redis_conn = get_redis_connection("default")
            lock_key = CacheKeyBuilder.seat_lock(showtime_id, seat_id)
            
            # SETNX: Set if Not eXists (atomic operation)
            acquired = redis_conn.setnx(lock_key, str(user_id))
            
            if acquired:
                # Set expiry
                redis_conn.expire(lock_key, timeout)
                logger.debug(f"Seat lock acquired: {seat_id} by user {user_id}")
                return True
            else:
                # Check if current user already holds the lock
                current_holder = redis_conn.get(lock_key)
                if current_holder and current_holder.decode('utf-8') == str(user_id):
                    # Re-acquire (extend TTL)
                    redis_conn.expire(lock_key, timeout)
                    logger.debug(f"Seat lock extended: {seat_id} by user {user_id}")
                    return True
                
                logger.debug(f"Seat lock failed: {seat_id} already locked by user {current_holder}")
                return False
                
        except Exception as e:
            logger.error(f"Error acquiring seat lock for {seat_id}: {e}")
            return False
    
    @staticmethod
    def unlock_seat(showtime_id, seat_id, user_id=None):
        """Release lock for a specific seat"""
        try:
            redis_conn = get_redis_connection("default")
            lock_key = CacheKeyBuilder.seat_lock(showtime_id, seat_id)
            
            if user_id:
                # Only unlock if current user holds the lock
                current_holder = redis_conn.get(lock_key)
                if current_holder and current_holder.decode('utf-8') == str(user_id):
                    redis_conn.delete(lock_key)
                    logger.debug(f"Seat unlocked: {seat_id} by user {user_id}")
            else:
                # Force unlock (admin/cleanup)
                redis_conn.delete(lock_key)
                logger.debug(f"Seat force-unlocked: {seat_id}")
                
        except Exception as e:
            logger.error(f"Error unlocking seat {seat_id}: {e}")
    
    @staticmethod
    def reserve_seats(showtime_id, seat_ids, user_id):
        """
        🔐 ATOMIC: Reserve multiple seats with rollback on failure
        WHY: Prevents race conditions and double bookings
        HOW: Uses SETNX for atomic locking, rolls back on any failure
        """
        if not seat_ids:
            return False
        
        # Step 1: Validate seats are available in database
        available_seats = SeatManager.get_available_seats(showtime_id)
        for seat_id in seat_ids:
            if seat_id not in available_seats:
                logger.warning(f"Seat {seat_id} not available for showtime {showtime_id}")
                return False
        
        # Step 2: Try to acquire all locks atomically
        acquired_locks = []
        try:
            for seat_id in seat_ids:
                if SeatManager.lock_seat_atomic(showtime_id, seat_id, user_id, 
                                               timeout=CacheTimeouts.SEAT_LOCK):
                    acquired_locks.append(seat_id)
                else:
                    # Lock acquisition failed - rollback all
                    logger.warning(f"Failed to lock seat {seat_id}, rolling back {len(acquired_locks)} locks")
                    for locked_seat in acquired_locks:
                        SeatManager.unlock_seat(showtime_id, locked_seat, user_id)
                    return False
            
            # All locks acquired successfully
            logger.info(f"Successfully reserved {len(seat_ids)} seats for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error reserving seats: {e}")
            # Rollback on error
            for locked_seat in acquired_locks:
                SeatManager.unlock_seat(showtime_id, locked_seat, user_id)
            return False
    
    @staticmethod
    def release_seats(showtime_id, seat_ids=None, user_id=None):
        """Release seat locks"""
        try:
            if seat_ids:
                # Release specific seats
                for seat_id in seat_ids:
                    SeatManager.unlock_seat(showtime_id, seat_id, user_id)
                logger.info(f"Released {len(seat_ids)} seats for showtime {showtime_id}")
            elif user_id:
                # Release all seats held by user
                # Get user's reservation from cache
                user_res_key = CacheKeyBuilder.user_reservation(showtime_id, user_id)
                user_res = cache.get(user_res_key)
                if user_res and 'seat_ids' in user_res:
                    for seat_id in user_res['seat_ids']:
                        SeatManager.unlock_seat(showtime_id, seat_id, user_id)
                    cache.delete(user_res_key)
                    logger.info(f"Released all seats for user {user_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error releasing seats: {e}")
            return False
    
    @staticmethod
    def confirm_seats(showtime_id, seat_ids):
        """
        ✅ Confirm seats (booking complete)
        - Release locks
        - Invalidate cache
        """
        try:
            # Release locks
            for seat_id in seat_ids:
                SeatManager.unlock_seat(showtime_id, seat_id)
            
            # Invalidate cache to reflect new availability
            CacheInvalidator.invalidate_showtime_cache(showtime_id)
            
            logger.info(f"Confirmed {len(seat_ids)} seats for showtime {showtime_id}")
            return True
        except Exception as e:
            logger.error(f"Error confirming seats: {e}")
            return False
    
    @staticmethod
    def release_seat(showtime_id, seat_id):
        """Release a single seat (convenience method)"""
        return SeatManager.unlock_seat(showtime_id, seat_id)


# ==============================================================================
# 💰 PRICE CALCULATOR (Unchanged, but included for completeness)
# ==============================================================================

class PriceCalculator:
    """Price calculation utilities"""
    
    TAX_RATE = Decimal('0.18')  # 18% GST
    CONVENIENCE_FEE = Decimal('30.00')
    
    @staticmethod
    def calculate_booking_amount(showtime, seat_count, seat_type='standard'):
        """Calculate booking amount with taxes"""
        base_price = showtime.price * seat_count
        
        # Seat type multipliers
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
