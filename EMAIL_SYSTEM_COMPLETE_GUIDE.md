# 📧 Email System - Complete Technical Guide

## 🎯 Overview

This document explains **exactly how the email system works** in the Movie Booking System, from start to finish. No external SDKs or complex libraries - just Django, Python standard library, and SMTP.

---

## 🔍 Table of Contents

1. [How It Works (High Level)](#how-it-works-high-level)
2. [Technology Stack](#technology-stack)
3. [Email Flow (Detailed)](#email-flow-detailed)
4. [Django Email System](#django-email-system)
5. [Template Rendering](#template-rendering)
6. [QR Code Generation](#qr-code-generation)
7. [SMTP Configuration](#smtp-configuration)
8. [Celery Integration](#celery-integration)
9. [Complete Code Walkthrough](#complete-code-walkthrough)
10. [Testing & Debugging](#testing--debugging)

---

## 🚀 How It Works (High Level)

```
USER ACTION → DJANGO VIEW → CELERY TASK → EMAIL UTILS → SMTP → USER'S INBOX
```

**Simple Explanation:**
1. User does something (books ticket, registers, etc.)
2. Django triggers an email task
3. Celery runs the task in background (async)
4. Email utility renders HTML/text templates
5. Generates QR code (if needed)
6. Sends email via Gmail's SMTP server
7. User receives professional email

**Key Point:** We're using **standard SMTP protocol** - no Google SDK, no third-party APIs. Just Python sending emails like any email client would.

---

## 🛠️ Technology Stack

### Core Technologies:
```python
# NO external SDKs needed! Just these Python packages:

1. Django (built-in email system)
   - django.core.mail
   - django.template.loader

2. Python Standard Library
   - smtplib (SMTP protocol)
   - email (email formatting)
   - base64 (encoding)
   - io.BytesIO (in-memory files)

3. Third-party Packages
   - qrcode (QR code generation)
   - Pillow (image processing)
   - celery (async tasks)
```

### What We're NOT Using:
❌ No Google API SDK  
❌ No SendGrid SDK  
❌ No Mailgun SDK  
❌ No AWS SES SDK  
❌ No third-party email services

### What We ARE Using:
✅ Standard SMTP protocol  
✅ Gmail's SMTP server  
✅ Django's built-in email system  
✅ Python's standard libraries  

---

## 📊 Email Flow (Detailed)

### Example: Booking Confirmation Email

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: User Completes Payment                                  │
│ - User pays on Razorpay modal                                   │
│ - Razorpay redirects back with payment details                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Django View (bookings/views.py)                        │
│                                                                  │
│ def verify_payment(request):                                    │
│     # Verify Razorpay signature                                 │
│     # Update booking status to CONFIRMED                        │
│     # Trigger email task                                        │
│     send_booking_confirmation_email.delay(booking.id)  ← ASYNC  │
│     return redirect('booking_detail')                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Celery Task Queue                                       │
│ - Task added to Redis queue                                     │
│ - Celery worker picks up task                                   │
│ - Runs in background (doesn't block user)                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Email Utility (bookings/email_utils.py)                │
│                                                                  │
│ @shared_task                                                    │
│ def send_booking_confirmation_email(booking_id):                │
│     # Fetch booking from database                               │
│     booking = Booking.objects.get(id=booking_id)                │
│                                                                  │
│     # Generate QR code                                          │
│     qr_data = f"Booking: {booking.booking_number}..."           │
│     qr_image = generate_qr_code(qr_data)                        │
│                                                                  │
│     # Prepare context data                                      │
│     context = {                                                 │
│         'user': booking.user,                                   │
│         'booking': booking,                                     │
│         'movie': booking.showtime.movie,                        │
│         'qr_code': base64_encoded_qr,                           │
│     }                                                            │
│                                                                  │
│     # Render templates                                          │
│     html = render_to_string('email_templates/...html', context) │
│     text = render_to_string('email_templates/...txt', context)  │
│                                                                  │
│     # Create and send email                                     │
│     email = EmailMultiAlternatives(...)                         │
│     email.send()                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Django's Email Backend                                  │
│                                                                  │
│ - Uses Python's smtplib (standard library)                      │
│ - Connects to smtp.gmail.com:587                                │
│ - Authenticates with email/password                             │
│ - Sends email using SMTP protocol                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Gmail SMTP Server                                       │
│ - Receives email from our server                                │
│ - Validates credentials                                         │
│ - Routes to recipient                                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: User's Email Client                                     │
│ - Gmail/Outlook/Apple Mail receives email                       │
│ - Displays professional HTML template                           │
│ - Shows QR code attachment                                      │
│ - User can view ticket                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📧 Django Email System

### How Django Sends Emails (Under the Hood)

Django's email system is a wrapper around Python's standard `smtplib`. Here's what happens:

```python
# When you call:
email.send()

# Django does this internally:
1. Reads EMAIL_* settings from settings.py/.env
2. Creates SMTP connection: smtplib.SMTP('smtp.gmail.com', 587)
3. Starts TLS encryption: smtp.starttls()
4. Authenticates: smtp.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
5. Formats email with headers, body, attachments
6. Sends: smtp.send_message(email_message)
7. Closes connection: smtp.quit()
```

### Configuration (settings.py)

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'          # Gmail's SMTP server
EMAIL_PORT = 587                        # TLS port
EMAIL_USE_TLS = True                    # Enable encryption
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'app-password'    # Gmail App Password
DEFAULT_FROM_EMAIL = 'MovieBooking <your-email@gmail.com>'
```

### What Each Setting Does:

| Setting | Purpose | Example |
|---------|---------|---------|
| `EMAIL_BACKEND` | Which Django backend to use | SMTP (default), Console (testing), File (development) |
| `EMAIL_HOST` | SMTP server address | `smtp.gmail.com`, `smtp.office365.com` |
| `EMAIL_PORT` | SMTP port | `587` (TLS), `465` (SSL), `25` (unencrypted) |
| `EMAIL_USE_TLS` | Enable encryption | `True` (recommended) |
| `EMAIL_HOST_USER` | SMTP username | Your email address |
| `EMAIL_HOST_PASSWORD` | SMTP password | App password (not regular password) |
| `DEFAULT_FROM_EMAIL` | Default sender | Display name + email |

---

## 🎨 Template Rendering

### How Templates Work

Django templates are HTML/text files with placeholders for dynamic content:

```html
<!-- email_templates/booking_confirmation.html -->
<h1>Hello {{ user.username }}!</h1>
<p>Your booking {{ booking.booking_number }} is confirmed.</p>
<p>Movie: {{ movie.title }}</p>
```

### Rendering Process

```python
# 1. Prepare context data (dictionary of variables)
context = {
    'user': user_object,           # Django User model
    'booking': booking_object,     # Django Booking model
    'movie': movie_object,         # Django Movie model
    'showtime': showtime_object,   # Django Showtime model
    'qr_code': 'base64string',     # Generated QR code
}

# 2. Render template with context
from django.template.loader import render_to_string

html_content = render_to_string(
    'email_templates/booking_confirmation.html',  # Template path
    context                                        # Data to inject
)

# Result: HTML string with all {{ variables }} replaced with actual data
```

### Template Variables Explained

**User Object:**
```python
user.username          # "john_doe"
user.email            # "john@example.com"
user.get_full_name()  # "John Doe"
```

**Booking Object:**
```python
booking.booking_number      # "BK001"
booking.total_amount        # 500
booking.get_seats_display() # "A1, A2, A3"
booking.status             # "CONFIRMED"
```

**Movie Object:**
```python
movie.title           # "Inception"
movie.genre          # "Sci-Fi"
movie.duration       # 148 (minutes)
movie.poster.url     # "/media/posters/inception.jpg"
```

**Template Filters:**
```django
{{ user.username|upper }}              → "JOHN_DOE"
{{ booking.created_at|date:"d M Y" }}  → "04 Jan 2026"
{{ movie.title|truncatewords:5 }}      → "Inception: The Movie..."
{{ value|default:"N/A" }}              → Shows "N/A" if value is None
```

---

## 🔲 QR Code Generation

### How QR Codes Work

```python
import qrcode
import base64
from io import BytesIO

# 1. Create QR code data (text to encode)
qr_data = f"""
Booking ID: {booking.booking_number}
Movie: {booking.showtime.movie.title}
Theater: {booking.showtime.screen.theater.name}
Date: {booking.showtime.date}
Time: {booking.showtime.start_time}
Seats: {booking.get_seats_display()}
"""

# 2. Generate QR code image
qr = qrcode.QRCode(
    version=1,           # Size (1-40, auto-adjusts)
    box_size=10,         # Pixels per box
    border=5,            # Border size
)
qr.add_data(qr_data)     # Add the text data
qr.make(fit=True)        # Optimize size

# 3. Create image
img = qr.make_image(
    fill_color="black",   # QR code color
    back_color="white"    # Background color
)

# 4. Convert to PNG in memory (not saved to disk)
buffer = BytesIO()
img.save(buffer, format="PNG")
qr_image_bytes = buffer.getvalue()

# 5. Encode to base64 (for embedding in HTML)
qr_base64 = base64.b64encode(qr_image_bytes).decode()

# 6. Use in email
# A) Embed in HTML:
#    <img src="data:image/png;base64,{{ qr_code }}">
# B) Attach as file:
#    email.attach('ticket.png', qr_image_bytes, 'image/png')
```

### Why Base64 Encoding?

- QR code is an image (binary data)
- Email HTML needs text format
- Base64 converts binary → text string
- Browser/email client decodes it back to image

**Example:**
```
Binary: [89 50 4E 47 0D 0A 1A 0A ...]  (PNG file)
Base64: iVBORw0KGgoAAAANSUhEUgAA...     (Text string)
HTML:   <img src="data:image/png;base64,iVBORw0KGgo...">
```

---

## 🔐 SMTP Configuration

### Gmail SMTP Setup

**Step 1: Enable 2-Factor Authentication**
- Go to Google Account settings
- Security → 2-Step Verification → Enable

**Step 2: Create App Password**
- Google Account → Security → App passwords
- Select "Mail" and your device
- Google generates 16-character password
- Example: `abcd efgh ijkl mnop`

**Step 3: Configure in .env**
```bash
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop  # No spaces!
```

### How SMTP Works

```
CLIENT (Our Django App)  ←→  SMTP SERVER (Gmail)  ←→  RECIPIENT

1. CONNECT
   Django: "Hello, I want to send email"
   Gmail:  "OK, connected on port 587"

2. STARTTLS
   Django: "Start encryption"
   Gmail:  "TLS enabled, connection secured"

3. AUTH
   Django: "Username: user@gmail.com"
   Gmail:  "Password?"
   Django: "Password: app-password"
   Gmail:  "Authenticated ✓"

4. MAIL FROM
   Django: "Sending from: moviebooking@gmail.com"
   Gmail:  "OK ✓"

5. RCPT TO
   Django: "Sending to: user@example.com"
   Gmail:  "OK ✓"

6. DATA
   Django: "Here's the email content..."
   Gmail:  "Received, will deliver ✓"

7. QUIT
   Django: "Goodbye"
   Gmail:  "Connection closed"
```

### Alternative SMTP Providers

**Gmail:**
```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
```

**Outlook/Office365:**
```python
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
```

**Yahoo:**
```python
EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 587
```

**Custom Domain (cPanel/Plesk):**
```python
EMAIL_HOST = 'mail.yourdomain.com'
EMAIL_PORT = 587
```

---

## ⚡ Celery Integration

### Why Celery?

**Without Celery:**
```python
def verify_payment(request):
    # ... verify payment ...
    send_booking_confirmation_email(booking.id)  # ← BLOCKS for 2-3 seconds
    return redirect('booking_detail')            # User waits...
```

**With Celery:**
```python
def verify_payment(request):
    # ... verify payment ...
    send_booking_confirmation_email.delay(booking.id)  # ← Returns instantly
    return redirect('booking_detail')                  # User redirected immediately
```

### How Celery Works

```
┌─────────────────┐
│  Django View    │
│  (User request) │
└────────┬────────┘
         │ .delay(booking_id)
         ↓
┌─────────────────┐
│  Redis Queue    │  ← Task stored here
│  [Task 1, 2, 3] │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Celery Worker   │  ← Separate process
│ (Background)    │     Picks up tasks
│ ┌─────────────┐ │     Runs them async
│ │   send_     │ │
│ │   email()   │ │
│ └─────────────┘ │
└─────────────────┘
```

### Celery Configuration

**1. Install:**
```bash
pip install celery redis
```

**2. Configure (moviebooking/celery.py):**
```python
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')

app = Celery('moviebooking')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

**3. Settings (settings.py):**
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
```

**4. Run Worker:**
```bash
celery -A moviebooking worker -l info
```

---

## 💻 Complete Code Walkthrough

### File: bookings/email_utils.py

```python
"""
Complete email sending utility with detailed explanations
"""

# ============================================================================
# IMPORTS
# ============================================================================

# Standard library - no external SDKs!
import logging          # For logging email events
import qrcode          # Generate QR codes
import base64          # Encode binary data to text
from io import BytesIO # In-memory file handling

# Django built-in email system
from django.core.mail import EmailMultiAlternatives  # Send HTML + text emails
from django.template.loader import render_to_string  # Render templates
from django.conf import settings                     # Access settings

# Celery for async tasks
from celery import shared_task

# Initialize logger
logger = logging.getLogger(__name__)


# ============================================================================
# BOOKING CONFIRMATION EMAIL
# ============================================================================

@shared_task  # ← Makes this function run asynchronously via Celery
def send_booking_confirmation_email(booking_id):
    """
    Sends booking confirmation email with QR code ticket
    
    FLOW:
    1. Fetch booking data from database
    2. Generate QR code with booking details
    3. Prepare context data for template
    4. Render HTML and text templates
    5. Create email with both versions
    6. Attach QR code as PNG file
    7. Send via SMTP
    
    HOW IT WORKS:
    - NO external APIs or SDKs
    - Uses Django's built-in email system
    - Django uses Python's smtplib (standard library)
    - SMTP = Simple Mail Transfer Protocol (like sending from Outlook)
    """
    
    # Import here to avoid circular imports
    from .models import Booking
    
    try:
        # ====================================================================
        # STEP 1: GET DATA FROM DATABASE
        # ====================================================================
        booking = Booking.objects.get(id=booking_id)
        user = booking.user
        
        logger.info(f"📧 Generating confirmation email for {booking.booking_number}")
        
        
        # ====================================================================
        # STEP 2: GENERATE QR CODE
        # ====================================================================
        
        # Create text data to encode in QR code
        qr_data = (
            f"Booking ID: {booking.booking_number}\n"
            f"Movie: {booking.showtime.movie.title}\n"
            f"Theater: {booking.showtime.screen.theater.name}\n"
            f"Date: {booking.showtime.date}\n"
            f"Time: {booking.showtime.start_time}\n"
            f"Seats: {booking.get_seats_display()}"
        )
        
        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to PNG in memory (not saved to disk)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_image = buffer.getvalue()  # Binary PNG data
        
        # Encode to base64 for embedding in HTML
        qr_base64 = base64.b64encode(qr_image).decode()
        
        
        # ====================================================================
        # STEP 3: PREPARE TEMPLATE CONTEXT
        # ====================================================================
        
        # Dictionary of variables to pass to template
        context = {
            'user': user,                      # Django User model instance
            'booking': booking,                # Django Booking model instance
            'movie': booking.showtime.movie,   # Related Movie object
            'showtime': booking.showtime,      # Related Showtime object
            'theater': booking.showtime.screen.theater,  # Related Theater
            'qr_code': qr_base64,             # Base64 encoded QR image
            'total_amount': booking.total_amount,
        }
        
        
        # ====================================================================
        # STEP 4: RENDER TEMPLATES
        # ====================================================================
        
        # Render HTML version (for modern email clients)
        html_content = render_to_string(
            'email_templates/booking_confirmation.html',
            context
        )
        # Result: HTML string with all {{ variables }} replaced
        
        # Render plain text version (for old email clients or accessibility)
        text_content = render_to_string(
            'email_templates/booking_confirmation.txt',
            context
        )
        
        
        # ====================================================================
        # STEP 5: CREATE EMAIL
        # ====================================================================
        
        subject = f'🎬 Booking Confirmed - {booking.booking_number}'
        from_email = settings.DEFAULT_FROM_EMAIL  # From .env
        to_email = [user.email]                   # Recipient list
        
        # EmailMultiAlternatives = Email with HTML + text versions
        email = EmailMultiAlternatives(
            subject,        # Email subject
            text_content,   # Plain text body (fallback)
            from_email,     # Sender
            to_email        # Recipients (list)
        )
        
        # Attach HTML version as alternative
        email.attach_alternative(html_content, "text/html")
        
        # Attach QR code as PNG file
        email.attach(
            f'booking_{booking.booking_number}.png',  # Filename
            qr_image,                                  # Binary data
            'image/png'                                # MIME type
        )
        
        
        # ====================================================================
        # STEP 6: SEND EMAIL
        # ====================================================================
        
        # This is where Django's email backend connects to SMTP
        email.send()
        
        # What happens internally:
        # 1. Django reads EMAIL_* settings from settings.py
        # 2. Creates SMTP connection to smtp.gmail.com:587
        # 3. Starts TLS encryption
        # 4. Authenticates with email/password
        # 5. Sends email using SMTP protocol
        # 6. Closes connection
        
        logger.info(f"✅ Email sent successfully to {user.email}")
        return f"Email sent to {user.email}"
        
    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}")
        return f"Error: {str(e)}"


# ============================================================================
# PAYMENT FAILED EMAIL
# ============================================================================

@shared_task
def send_payment_failed_email(booking_id):
    """
    Sends email when payment fails or is cancelled
    
    SIMPLER THAN CONFIRMATION:
    - No QR code needed
    - Just HTML/text templates
    - Same SMTP process
    """
    from .models import Booking
    
    try:
        booking = Booking.objects.get(id=booking_id)
        user = booking.user
        
        logger.info(f"📧 Sending payment failed email for {booking.booking_number}")
        
        # Prepare context
        context = {
            'user': user,
            'booking': booking,
            'movie': booking.showtime.movie,
        }
        
        # Render templates
        text_content = render_to_string(
            'email_templates/payment_failed.txt',
            context
        )
        html_content = render_to_string(
            'email_templates/payment_failed.html',
            context
        )
        
        # Create and send email
        subject = f'❌ Payment Failed - Booking {booking.booking_number}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email]
        
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send()  # ← SMTP happens here
        
        logger.info(f"✅ Payment failed email sent to {user.email}")
        return f"Email sent to {user.email}"
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"


# ============================================================================
# SHOWTIME REMINDER EMAIL
# ============================================================================

@shared_task
def send_seat_reminder_email(booking_id):
    """
    Sends reminder email 24 hours before showtime
    
    TRIGGERED BY:
    - Celery Beat (scheduled task)
    - Runs daily, checks which movies are tomorrow
    """
    from .models import Booking
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Only send if booking is confirmed
        if booking.status != 'CONFIRMED':
            logger.warning(f"⚠️ Booking {booking.booking_number} not confirmed")
            return "Booking not confirmed"
        
        logger.info(f"📧 Sending reminder for {booking.booking_number}")
        
        # Prepare context
        context = {
            'booking': booking,
            'user': booking.user,
            'movie': booking.showtime.movie,
            'showtime': booking.showtime,
            'theater': booking.showtime.screen.theater,
        }
        
        # Render templates
        text_content = render_to_string(
            'email_templates/showtime_reminder.txt',
            context
        )
        html_content = render_to_string(
            'email_templates/showtime_reminder.html',
            context
        )
        
        # Send email
        subject = f'⏰ Reminder: "{booking.showtime.movie.title}" starts soon!'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [booking.user.email]
        
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"✅ Reminder sent for {booking.booking_number}")
        return f"Reminder sent"
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"
```

---

## 🧪 Testing & Debugging

### Test 1: Check Email Configuration

```python
python manage.py shell

from django.conf import settings
print("Host:", settings.EMAIL_HOST)
print("Port:", settings.EMAIL_PORT)
print("User:", settings.EMAIL_HOST_USER)
print("Password set:", bool(settings.EMAIL_HOST_PASSWORD))
```

### Test 2: Send Simple Test Email

```python
from django.core.mail import send_mail

result = send_mail(
    subject='Test Email',
    message='If you receive this, SMTP works!',
    from_email=settings.EMAIL_HOST_USER,
    recipient_list=[settings.EMAIL_HOST_USER],
    fail_silently=False,
)

print(f"Sent: {result} email(s)")
# Result = 1 means success
```

### Test 3: Test Template Rendering

```python
from django.template.loader import render_to_string

context = {
    'user': {'username': 'TestUser'},
    'booking': {'booking_number': 'TEST123'},
    'movie': {'title': 'Test Movie'},
}

html = render_to_string('email_templates/booking_confirmation.html', context)
print("Length:", len(html), "characters")
print("Contains booking number:", 'TEST123' in html)
```

### Test 4: Generate QR Code

```python
import qrcode
from io import BytesIO
import base64

qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data("Test Data")
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
buffer = BytesIO()
img.save(buffer, format="PNG")

print("QR code size:", len(buffer.getvalue()), "bytes")
```

### Test 5: Send Full Email

```python
from bookings.email_utils import send_booking_confirmation_email

# For a real booking
result = send_booking_confirmation_email(1)
print(result)

# Check your email inbox!
```

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `SMTPAuthenticationError` | Wrong password | Check App Password (no spaces!) |
| `SMTPServerDisconnected` | Network/firewall | Check internet, firewall rules |
| `Template not found` | Wrong path | Verify `TEMPLATES['DIRS']` in settings |
| `QR code error` | Missing package | `pip install qrcode[pil]` |
| `Celery not picking up` | Worker not running | Start worker: `celery -A moviebooking worker` |
| Email not received | Spam folder | Check spam, verify recipient email |

---

## 📊 Summary Diagram

```
╔════════════════════════════════════════════════════════════════════╗
║                   EMAIL SYSTEM ARCHITECTURE                        ║
╚════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────┐
│                         TECHNOLOGY STACK                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ✅ Django (built-in email system)                               │
│     └─ django.core.mail.EmailMultiAlternatives                   │
│                                                                   │
│  ✅ Python Standard Library (NO SDKs!)                           │
│     ├─ smtplib (SMTP protocol)                                   │
│     ├─ email (message formatting)                                │
│     ├─ base64 (encoding)                                         │
│     └─ io.BytesIO (in-memory files)                              │
│                                                                   │
│  ✅ Third-party Packages                                         │
│     ├─ qrcode (QR generation)                                    │
│     ├─ Pillow (image processing)                                 │
│     └─ celery (async tasks)                                      │
│                                                                   │
│  ✅ Gmail SMTP Server                                            │
│     └─ smtp.gmail.com:587 (TLS)                                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                           DATA FLOW                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. USER ACTION                                                   │
│     └─ Books ticket, completes payment                           │
│                                                                   │
│  2. DJANGO VIEW                                                   │
│     └─ Triggers: send_booking_confirmation_email.delay(id)       │
│                                                                   │
│  3. CELERY QUEUE (Redis)                                         │
│     └─ Stores task for background processing                     │
│                                                                   │
│  4. CELERY WORKER                                                 │
│     └─ Picks up and executes task async                          │
│                                                                   │
│  5. EMAIL UTILS (bookings/email_utils.py)                        │
│     ├─ Fetch booking data from database                          │
│     ├─ Generate QR code (qrcode library)                         │
│     ├─ Prepare context data (dictionary)                         │
│     ├─ Render HTML template (Django template engine)             │
│     ├─ Render text template (fallback)                           │
│     └─ Create EmailMultiAlternatives object                      │
│                                                                   │
│  6. DJANGO EMAIL BACKEND                                          │
│     ├─ Opens SMTP connection (smtplib)                           │
│     ├─ Connects to smtp.gmail.com:587                            │
│     ├─ Starts TLS encryption                                     │
│     ├─ Authenticates with credentials                            │
│     ├─ Sends email using SMTP protocol                           │
│     └─ Closes connection                                         │
│                                                                   │
│  7. GMAIL SMTP SERVER                                             │
│     ├─ Receives email                                            │
│     ├─ Validates sender                                          │
│     └─ Routes to recipient                                       │
│                                                                   │
│  8. USER'S INBOX                                                  │
│     └─ Professional email with QR ticket                         │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                       KEY COMPONENTS                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📁 /email_templates/           → HTML/text templates            │
│  📄 bookings/email_utils.py     → Email sending logic            │
│  ⚙️  moviebooking/settings.py   → Email configuration            │
│  🔐 .env                        → SMTP credentials               │
│  📦 requirements.txt            → Dependencies                   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎓 Key Takeaways

### What We're Using:
1. **Django's Built-in Email System** - No external SDKs
2. **Python's Standard Library** - smtplib for SMTP
3. **Gmail's SMTP Server** - Standard email protocol
4. **Django Templates** - For HTML/text rendering
5. **QRCode Library** - Simple Python package
6. **Celery** - For async processing
7. **Redis** - Task queue for Celery

### What Makes It Work:
- **SMTP Protocol** - Universal email standard (like HTTP for web)
- **Template Rendering** - Django replaces {{ variables }} with real data
- **Base64 Encoding** - Converts binary images to text for HTML
- **Async Processing** - Celery runs email tasks in background
- **Multi-part Emails** - Both HTML and plain text versions

### No Magic, No SDKs:
- ✅ Just Python standard library (smtplib)
- ✅ Django's wrapper around smtplib
- ✅ SMTP = same protocol Outlook/Thunderbird use
- ✅ Works with any SMTP server (Gmail, Yahoo, custom)
- ✅ No API keys, no quotas, no external dependencies

---

## 📚 Additional Resources

### Learn More:
- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [Python smtplib](https://docs.python.org/3/library/smtplib.html)
- [SMTP Protocol (RFC 5321)](https://tools.ietf.org/html/rfc5321)
- [Django Templates](https://docs.djangoproject.com/en/stable/topics/templates/)
- [Celery Documentation](https://docs.celeryproject.org/)

### Tools for Testing:
- [MailHog](https://github.com/mailhog/MailHog) - Local email testing
- [Mailtrap](https://mailtrap.io/) - Email sandbox
- [Email Acid](https://www.emailonacid.com/) - Email client testing

---

**Last Updated:** January 4, 2026  
**Author:** Movie Booking System Development Team  
**Status:** ✅ Complete & Production Ready

---

