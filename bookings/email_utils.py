"""
❓ WHY THIS FILE EXISTS:
Centralizes all email communication logic. It handles template rendering, 
QR code generation, and uses Celery to send emails asynchronously.
"""
import qrcode
import base64
from io import BytesIO
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def send_booking_confirmation_email(booking_id):
    """
    📧 HOW: Confirmation Email with Ticket
    - Renders the HTML/Text templates.
    - Generates a QR Code containing booking details.
    - Encodes it as Base64 to embed in the email.
    ❓ WHY: Provides the user with a digital ticket they can show at the theater.
    """
    from .models import Booking
    try:
        booking = Booking.objects.get(id=booking_id)
        user = booking.user
        
        # Generate QR Code
        qr_data = (f"Booking ID: {booking.booking_number}\n"
                   f"Movie: {booking.showtime.movie.title}\n"
                   f"Theater: {booking.showtime.screen.theater.name}\n"
                   f"Date: {booking.showtime.date}\n"
                   f"Time: {booking.showtime.start_time}\n"
                   f"Seats: {booking.get_seats_display()}")
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_image = buffer.getvalue()
        qr_base64 = base64.b64encode(qr_image).decode()
        
        context = {
            'booking': booking,
            'user': user,
            'movie': booking.showtime.movie,
            'showtime': booking.showtime,
            'theater': booking.showtime.screen.theater,
            'qr_code': qr_base64,
            'total_amount': booking.total_amount,
        }
        
        text_content = render_to_string('bookings/emails/booking_confirmation.txt', context)
        html_content = render_to_string('bookings/emails/booking_confirmation.html', context)
        
        subject = f'🎬 Booking Confirmed - {booking.booking_number}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email]
        
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.attach(f'booking_{booking.booking_number}.png', qr_image, 'image/png')
        # To embed in HTML, we use CID
        # But for simplicity in this template restoration, we just attach it
        
        email.send()
        return f"Email sent successfully to {user.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"

@shared_task
def send_payment_failed_email(booking_id):
    """Send payment failed email"""
    from .models import Booking
    
    try:
        booking = Booking.objects.get(id=booking_id)
        user = booking.user
        
        context = {
            'booking': booking,
            'user': user,
            'movie': booking.showtime.movie,
        }
        
        text_content = render_to_string('bookings/emails/payment_failed.txt', context)
        html_content = render_to_string('bookings/emails/payment_failed.html', context)
        
        subject = f'❌ Payment Failed - Booking {booking.booking_number}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email]
        
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        return f"Payment failed email sent to {user.email}"
    except Exception as e:
        return f"Error sending payment failed email: {str(e)}"

@shared_task
def send_seat_reminder_email(booking_id):
    """Send reminder email before showtime"""
    from .models import Booking
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        context = {
            'booking': booking,
            'user': booking.user,
            'movie': booking.showtime.movie,
            'showtime': booking.showtime,
            'theater': booking.showtime.screen.theater,
        }
        
        text_content = render_to_string('bookings/emails/booking_confirmation.txt', context) # Reusing for now
        html_content = render_to_string('bookings/emails/booking_confirmation.html', context)
        
        subject = f'⏰ Reminder: Your movie starts soon!'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [booking.user.email]
        
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        return f"Reminder sent for booking {booking.booking_number}"
    except Exception as e:
        return f"Error sending reminder: {str(e)}"