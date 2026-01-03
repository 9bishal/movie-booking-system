"""
🔧 Enhanced Celery Tasks with Distributed Locking
WHY: Prevents duplicate processing across multiple workers
WHAT: Background tasks with proper locking and error handling
WHEN: Scheduled by Celery Beat
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django_redis import get_redis_connection
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def release_expired_bookings(self):
    """
    🔒 WITH DISTRIBUTED LOCK
    WHY: Prevents multiple workers from processing the same bookings
    HOW: Uses Redis SETNX for distributed locking
    WHEN: Runs every minute via Celery Beat
    """
    redis_conn = get_redis_connection("default")
    lock_key = "celery_lock:release_expired_bookings"
    
    # Try to acquire distributed lock
    lock_acquired = redis_conn.setnx(lock_key, "locked")
    
    if not lock_acquired:
        logger.info("Another worker is already processing expired bookings - skipping")
        return "Skipped - lock held by another worker"
    
    try:
        # Set lock expiry (5 minutes max processing time)
        redis_conn.expire(lock_key, 300)
        
        # Import here to avoid circular imports
        from .models import Booking
        from .services import BookingService
        from .utils_enhanced import CacheInvalidator
        
        # Find expired PENDING bookings
        expired_bookings = Booking.objects.filter(
            status='PENDING',
            expires_at__lt=timezone.now()
        )
        
        released_count = 0
        failed_count = 0
        
        for booking in expired_bookings:
            try:
                # Use service layer for consistent expiration
                success, error = BookingService.expire_booking(booking)
                
                if success:
                    released_count += 1
                    # Invalidate cache
                    CacheInvalidator.invalidate_on_booking_expired(booking)
                    logger.info(f"Expired booking {booking.booking_number}")
                else:
                    failed_count += 1
                    logger.error(f"Failed to expire {booking.booking_number}: {error}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Exception expiring {booking.booking_number}: {e}")
        
        result = f"Released {released_count} expired bookings, {failed_count} failed"
        logger.info(f"Booking expiration complete: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in release_expired_bookings task: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        
    finally:
        # Always release the lock
        redis_conn.delete(lock_key)


@shared_task
def send_showtime_reminders():
    """
    ⏰ Send reminders for upcoming showtimes
    WHY: Customer service - remind users of their bookings
    HOW: Find confirmed bookings in next hour, send emails
    """
    try:
        from .models import Booking
        from .email_utils import send_seat_reminder_email
        
        now = timezone.now()
        reminder_time = now + timedelta(hours=1)
        
        # Find confirmed bookings with showtime in next hour
        bookings = Booking.objects.filter(
            status='CONFIRMED',
            showtime__date=reminder_time.date(),
            showtime__start_time__hour=reminder_time.hour
        )
        
        sent_count = 0
        
        for booking in bookings:
            try:
                send_seat_reminder_email.delay(booking.id)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to queue reminder for booking {booking.id}: {e}")
        
        result = f"Queued {sent_count} showtime reminders"
        logger.info(result)
        return result
        
    except Exception as e:
        logger.error(f"Error in send_showtime_reminders task: {e}")
        return f"Error: {e}"


@shared_task
def cleanup_old_data():
    """
    🧹 Archive old bookings
    WHY: Database health - remove old data
    HOW: Find bookings older than 30 days
    """
    try:
        from .models import Booking
        from datetime import date
        
        # Find bookings older than 30 days
        old_date = date.today() - timedelta(days=30)
        old_bookings = Booking.objects.filter(
            showtime__date__lt=old_date
        )
        
        count = old_bookings.count()
        
        # In production, archive instead of delete
        # For now, just log
        result = f"Found {count} old bookings to archive"
        logger.info(result)
        return result
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_data task: {e}")
        return f"Error: {e}"


@shared_task
def warm_cache_for_upcoming_shows():
    """
    🔥 Pre-warm cache for popular showtimes
    WHY: Performance - reduce cache misses for first users
    HOW: Pre-populate cache for upcoming shows
    WHEN: Runs every 30 minutes via Celery Beat
    """
    try:
        from movies.theater_models import Showtime
        from .utils_enhanced import SeatManager
        
        # Get upcoming showtimes (next 6 hours)
        now = timezone.now()
        upcoming_showtimes = Showtime.objects.filter(
            is_active=True,
            date__gte=now.date(),
            start_time__gte=now.time()
        ).order_by('date', 'start_time')[:20]  # Top 20 upcoming
        
        warmed_count = 0
        
        for showtime in upcoming_showtimes:
            try:
                # Pre-populate cache
                SeatManager.get_seat_layout(showtime.id)
                SeatManager.get_available_seats(showtime.id)
                warmed_count += 1
            except Exception as e:
                logger.error(f"Cache warming failed for showtime {showtime.id}: {e}")
        
        result = f"Warmed cache for {warmed_count} showtimes"
        logger.info(result)
        return result
        
    except Exception as e:
        logger.error(f"Error in warm_cache_for_upcoming_shows task: {e}")
        return f"Error: {e}"


@shared_task
def monitor_cache_health():
    """
    📊 Monitor cache health and log metrics
    WHY: Visibility into cache performance
    HOW: Check Redis connection, log stats
    """
    try:
        from django.core.cache import cache
        redis_conn = get_redis_connection("default")
        
        # Test Redis connectivity
        redis_conn.ping()
        
        # Get Redis info
        info = redis_conn.info()
        
        metrics = {
            'connected_clients': info.get('connected_clients', 0),
            'used_memory_human': info.get('used_memory_human', 'N/A'),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
        }
        
        # Calculate hit rate
        hits = metrics['keyspace_hits']
        misses = metrics['keyspace_misses']
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        result = f"Cache health: {hit_rate:.2f}% hit rate, {metrics['used_memory_human']} used"
        logger.info(result)
        logger.info(f"Cache metrics: {metrics}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in monitor_cache_health task: {e}")
        return f"Error: {e}"
