"""
❓ WHY THIS FILE EXISTS:
Centralizes all email communication logic. It handles template rendering, 
QR code generation, and uses Celery to send emails asynchronously.
"""
import logging
import qrcode
import base64
from io import BytesIO
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

# Initialize logger for tracking email events
logger = logging.getLogger(__name__)



@shared_task
def send_booking_confirmation_email(booking_id):
    """
    📧 HOW: Confirmation Email with Ticket
    - Renders the HTML/Text templates.
    - Generates a QR Code containing booking details.
    - Encodes it as Base64 to embed in the email.
    ❓ WHY: Provides the user with a digital ticket they can show at the theater.
    
    🛡️ CRITICAL CHECKS:
    - Only send if payment_received_at is set
    - Only send if status is CONFIRMED
    - Only send once (idempotency)
    """
    from .models import Booking
    from django.db import transaction
    
    try:
        # 🛡️ ATOMIC LOCK: Use select_for_update to ensure only one task processes this email
        # This prevents race conditions where multiple async tasks try to send the same email
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(id=booking_id)
            user = booking.user
            
            # 🛡️ CRITICAL: Only send if payment_received_at is set
            # This ensures we never send confirmation before payment is actually received
            if not booking.payment_received_at:
                logger.warning(
                    f"⏭️  Skipping confirmation email for {booking.booking_number} - "
                    f"payment_received_at not set (payment not received)"
                )
                return f"Email not sent - payment not received yet"
            
            # 🛡️ CRITICAL: Only send if booking is CONFIRMED
            # Don't send confirmation if payment failed
            if booking.status != 'CONFIRMED':
                logger.warning(
                    f"⏭️  Skipping confirmation email for {booking.booking_number} - "
                    f"Status is {booking.status}, not CONFIRMED (payment may have failed)"
                )
                return f"Email not sent - booking status is {booking.status}"
            
            # 🛡️ IDEMPOTENCY CHECK: Only send once
            # If email was already sent, don't send again (prevents double emails)
            if booking.confirmation_email_sent:
                logger.warning(
                    f"⏭️  Skipping confirmation email for {booking.booking_number} - "
                    f"Email already sent"
                )
                return f"Email already sent - skipping"
            
            # 🛡️ MARK AS PROCESSING: Set flag inside transaction to prevent concurrent sends
            booking.confirmation_email_sent = True
            booking.save()
        
        # Rest of the email sending happens OUTSIDE the transaction lock
        logger.info(f"📧 Generating confirmation email for booking {booking.booking_number}")
        
        # Use the standardized QR code from the booking model
        try:
            qr_base64 = booking.get_qr_code_base64()
            if not qr_base64:
                # Fallback: generate QR code inline if model method fails
                logger.warning(f"QR code generation failed for booking {booking.booking_number}, using fallback")
                qr_base64 = booking._generate_inline_qr_base64()
        except Exception as e:
            logger.error(f"QR code generation error for booking {booking.booking_number}: {str(e)}")
            # Generate simple fallback QR code
            qr_data = f"Booking: {booking.booking_number}\nMovie: {booking.showtime.movie.title}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Convert base64 back to bytes for email attachment
        qr_image_bytes = base64.b64decode(qr_base64)
        
        context = {
            'booking': booking,
            'user': user,
            'movie': booking.showtime.movie,
            'showtime': booking.showtime,
            'theater': booking.showtime.screen.theater,
            'qr_code': qr_base64,
            'total_amount': booking.total_amount,
        }
        
        text_content = render_to_string('booking_confirmation.txt', context)
        html_content = render_to_string('booking_confirmation.html', context)
        
        subject = f'🎬 Booking Confirmed - {booking.booking_number}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email]
        
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.attach(f'booking_{booking.booking_number}.png', qr_image_bytes, 'image/png')
        
        # Send email
        email.send()
        
        logger.info(f"✅ Confirmation email sent to {user.email}")
        return f"Email sent successfully to {user.email}"
    except Exception as e:
        logger.error(f"❌ Error sending email for booking {booking_id}: {str(e)}")
        return f"Error sending email: {str(e)}"

@shared_task
def send_payment_failed_email(booking_id):
    """
    ❌ Send payment failed email to user
    
    WHEN: Called when payment fails or is cancelled
    WHAT: Notifies user that payment failed and seats are released
    
    🛡️ CRITICAL LOGIC:
    - Never send if payment_received_at is set (payment succeeded)
    - Never send if status is CONFIRMED (payment succeeded)
    - Only send if in a failure state (FAILED, PENDING with no payment)
    """
    from .models import Booking
    from django.db import transaction
    
    try:
        # 🛡️ ATOMIC LOCK: Use select_for_update to ensure only one task processes this email
        # This prevents race conditions where multiple async tasks try to send the same email
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(id=booking_id)
            user = booking.user
            
            # 🛡️ CRITICAL CHECK 1: If payment_received_at is set, payment DEFINITELY succeeded
            # Don't send failure email at all
            if booking.payment_received_at:
                logger.warning(
                    f"⏭️  Skipping payment failed email for {booking.booking_number} - "
                    f"payment_received_at is set ({booking.payment_received_at}). Payment actually succeeded!"
                )
                return f"Email not sent - payment was received"
            
            # 🛡️ CRITICAL CHECK 2: Only send if booking is still FAILED
            # Don't send failure email if booking is CONFIRMED (payment succeeded)
            if booking.status != 'FAILED':
                logger.warning(
                    f"⏭️  Skipping payment failed email for {booking.booking_number} - "
                    f"Status is {booking.status}, not FAILED"
                )
                return f"Email not sent - booking status is {booking.status}"
            
            # 🛡️ IDEMPOTENCY CHECK: Only send once
            # If email was already sent, don't send again (prevents double emails)
            if booking.failure_email_sent:
                logger.warning(
                    f"⏭️  Skipping payment failed email for {booking.booking_number} - "
                    f"Email already sent"
                )
                return f"Email already sent - skipping"
            
            # 🛡️ MARK AS PROCESSING: Set flag inside transaction to prevent concurrent sends
            booking.failure_email_sent = True
            booking.save()
        
        # Rest of the email sending happens OUTSIDE the transaction lock
        logger.info(f"📧 Generating payment failed email for booking {booking.booking_number}")
        
        context = {
            'booking': booking,
            'user': user,
            'movie': booking.showtime.movie,
        }
        
        text_content = render_to_string('payment_failed.txt', context)
        html_content = render_to_string('payment_failed.html', context)
        
        subject = f'❌ Payment Failed - Booking {booking.booking_number}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email]
        
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"✅ Payment failed email sent to {user.email}")
        return f"Payment failed email sent to {user.email}"
    except Exception as e:
        logger.error(f"❌ Error sending payment failed email: {str(e)}")
        return f"Error sending payment failed email: {str(e)}"

@shared_task
def send_seat_reminder_email(booking_id):
    """
    ⏰ Send reminder email before showtime
    
    WHEN: Called ~24 hours before the movie
    WHAT: Reminds user about their booking and showtime
    """
    from .models import Booking
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Only send reminder if booking is confirmed
        if booking.status != 'CONFIRMED':
            logger.warning(f"⚠️ Booking {booking.booking_number} is not confirmed. Skipping reminder.")
            return f"Booking not confirmed. Reminder skipped."
        
        logger.info(f"📧 Generating reminder email for booking {booking.booking_number}")
        
        context = {
            'booking': booking,
            'user': booking.user,
            'movie': booking.showtime.movie,
            'showtime': booking.showtime,
            'theater': booking.showtime.screen.theater,
        }
        
        text_content = render_to_string('showtime_reminder.txt', context)
        html_content = render_to_string('showtime_reminder.html', context)
        
        subject = f'⏰ Reminder: Your movie "{booking.showtime.movie.title}" starts soon!'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [booking.user.email]
        
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"✅ Reminder email sent for booking {booking.booking_number}")
        return f"Reminder sent for booking {booking.booking_number}"
    except Exception as e:
        logger.error(f"❌ Error sending reminder email: {str(e)}")
        return f"Error sending reminder: {str(e)}"

@shared_task
def send_late_payment_email(booking_id):
    """
    💰 Send email when payment arrives AFTER 12-minute window expires
    
    WHEN: Payment received after booking.expires_at
    WHAT: Notify user of refund and suggest trying again
    
    🔐 SCENARIO:
    - User completes payment at 12:05 PM
    - But the 12-minute window expired at 12:12 PM (payment initiated at 12:00 PM)
    - So payment is marked FAILED and this email is sent
    - User is notified that refund will be processed within 24 hours
    """
    from .models import Booking
    
    try:
        booking = Booking.objects.get(id=booking_id)
        user = booking.user
        
        logger.info(
            f"📧 [LATE PAYMENT] Generating refund email for booking {booking.booking_number}\n"
            f"   Payment received at: {booking.payment_received_at}\n"
            f"   Window expired at: {booking.expires_at}\n"
            f"   Payment ID: {booking.payment_id}\n"
            f"   User: {user.email}"
        )
        
        context = {
            'booking': booking,
            'user': user,
            'movie': booking.showtime.movie,
            'showtime': booking.showtime,
            'theater': booking.showtime.screen.theater,
            'payment_received_at': booking.payment_received_at,
            'expires_at': booking.expires_at,
            'payment_id': booking.payment_id,
        }
        
        text_content = render_to_string('payment_late.txt', context)
        html_content = render_to_string('payment_late.html', context)
        
        subject = f'💰 Refund Initiated - Booking {booking.booking_number} (Payment After Timeout)'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email]
        
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"✅ [LATE PAYMENT] Refund email sent to {user.email} for booking {booking.booking_number}")
        
        # Mark booking with refund notification sent
        booking.refund_notification_sent = True
        booking.save(update_fields=['refund_notification_sent'])
        
        return f"Late payment refund email sent to {user.email}"
    except Exception as e:
        logger.error(
            f"❌ [LATE PAYMENT] Error sending refund email for booking {booking_id}: {str(e)}\n"
            f"   Exception type: {type(e).__name__}"
        )
        return f"Error sending late payment email: {str(e)}"