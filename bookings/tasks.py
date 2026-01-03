"""
❓ WHY THIS FILE EXISTS:
This file contains the logic for background jobs. It prevents the main website 
from getting slow by offloading long-running tasks (like email) or 
automated maintenance (like cleaning up old data) to a separate process.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def release_expired_bookings():
    """
    🧹 CLEANUP: Expire bookings past their payment window
    
    WHY: Automatically free seats when users don't pay within 12 minutes
    HOW: Find PENDING bookings past expires_at, use service layer to expire
    WHEN: Runs every minute via Celery Beat
    
    UPDATED: Now uses BookingService for consistent expiration logic
    """
    from .models import Booking
    from .services import BookingService
    import logging
    
    logger = logging.getLogger(__name__)

    # Find 'PENDING' bookings that have passed their 'expires_at' time
    expired_bookings = Booking.objects.filter(
        status='PENDING',
        expires_at__lt=timezone.now()
    )
    
    released_count = 0
    failed_count = 0
    
    for booking in expired_bookings:
        # Use service layer for consistent expiration
        success, error = BookingService.expire_booking(booking)
        
        if success:
            released_count += 1
            logger.info(f"Released seats for expired booking {booking.booking_number}")
        else:
            failed_count += 1
            logger.error(f"Failed to expire booking {booking.booking_number}: {error}")
    
    logger.info(f"Booking expiration task complete: {released_count} expired, {failed_count} failed")
    return f"Released {released_count} expired bookings, {failed_count} failed"

@shared_task
def send_showtime_reminders():
    """
    ⏰ WHY: Customer Service - Don't let users miss their movie!
    HOW: Find confirmed bookings for shows starting in the next hour and send reminders.
    """
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
        send_seat_reminder_email.delay(booking.id)
        sent_count += 1
    
    return f"Sent {sent_count} showtime reminders"

@shared_task
def cleanup_old_data():
    """
    🧹 WHY: Database Health - Records from a year ago don't need to be in the main table.
    HOW: Find bookings older than 30 days and archive/delete them. (Mocked for now)
    """
    from .models import Booking
    from datetime import date
    
    # Archive bookings older than 30 days
    old_date = date.today() - timedelta(days=30)
    old_bookings = Booking.objects.filter(
        showtime__date__lt=old_date
    )
    
    count = old_bookings.count()
    # In production, you might archive these instead of deleting
    # old_bookings.delete()
    
    return f"Found {count} old bookings to archive"