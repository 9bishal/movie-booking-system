# ⚙️ Understanding Celery in Movie Booking System
## A Beginner's Guide

---

## 📚 Table of Contents
1. [What is Celery?](#what-is-celery)
2. [Why We Need Celery](#why-we-need-celery)
3. [How Celery Works](#how-celery-works)
4. [Celery in Our System](#celery-in-our-system)
5. [Real-World Example](#real-world-example)
6. [Celery Beat (Scheduler)](#celery-beat-scheduler)
7. [Common Tasks](#common-tasks)
8. [Troubleshooting](#troubleshooting)

---

## 🤔 What is Celery?

**Celery** is a **task queue** system for Python. Think of it as a **robot assistant** that does background work while your main application keeps serving users.

### Simple Analogy 🎯
Imagine you're running a movie theater:

**Without Celery:**
```
Customer: "I want to book a ticket"
You: "Sure! Let me..."
      1. Check seat availability ⏱️ (2 seconds)
      2. Process payment ⏱️ (3 seconds)
      3. Send confirmation email ⏱️ (5 seconds)
      4. Print ticket ⏱️ (2 seconds)
Customer: *waits 12 seconds* 😴
You: "Here's your ticket!"
```

**With Celery:**
```
Customer: "I want to book a ticket"
You: "Sure! Let me..."
      1. Check seat availability ⏱️ (2 seconds)
      2. Process payment ⏱️ (3 seconds)
You: "Done! You'll get email shortly!" ✅
Customer: *happy, leaves in 5 seconds* 😊

[Meanwhile, Celery worker in background:]
      3. Send confirmation email ⏱️ (5 seconds)
      4. Print ticket ⏱️ (2 seconds)
      [Happens in background, customer doesn't wait!]
```

### Key Characteristics
- **Asynchronous**: Do work in the background, don't block users
- **Distributed**: Can run on multiple servers/workers
- **Reliable**: If a task fails, it can retry automatically
- **Scheduled**: Can run tasks on a schedule (like cron jobs)

---

## 🎯 Why We Need Celery

### Problems Without Celery ❌

#### Problem 1: Slow Response Times
```python
def book_ticket(user, showtime, seats):
    # Step 1: Process payment (3 seconds)
    payment = process_razorpay_payment()
    
    # Step 2: Send confirmation email (5 seconds)
    send_email(user.email, booking_details)
    
    # Step 3: Send SMS (3 seconds)
    send_sms(user.phone, booking_details)
    
    # User waited 11 seconds! 😫
    return "Booking confirmed"
```

#### Problem 2: Expired Bookings Pile Up
```python
# Without background cleanup, expired bookings stay as "PENDING" forever
# Admin has to manually find and expire them 😰
```

#### Problem 3: Email Failures Block Everything
```python
def book_ticket():
    payment = process_payment()  # Success ✅
    
    send_email()  # SMTP server down! ❌
    # Entire booking fails! 😱
    # But payment already processed! 💸
```

### Solutions With Celery ✅

#### Solution 1: Instant Response
```python
def book_ticket(user, showtime, seats):
    # Step 1: Process payment (3 seconds)
    payment = process_razorpay_payment()
    
    # Step 2: Queue background tasks (instant!)
    send_confirmation_email.delay(booking_id)  # Async!
    send_confirmation_sms.delay(booking_id)    # Async!
    
    # User sees response in 3 seconds! 😊
    return "Booking confirmed! Email coming soon"
```

#### Solution 2: Automatic Cleanup
```python
# Celery Beat runs this every minute
@periodic_task(run_every=60)
def cleanup_expired_bookings():
    expired = Booking.objects.filter(
        status='PENDING',
        expires_at__lt=now()
    )
    for booking in expired:
        booking.expire()
    # Automatic cleanup! 🎉
```

#### Solution 3: Fault Tolerance
```python
@task(bind=True, max_retries=3)
def send_email(self, booking_id):
    try:
        # Try sending email
        email.send()
    except SMTPException:
        # Retry after 5 minutes
        self.retry(countdown=300)
        # Booking still succeeded! ✅
```

---

## ⚙️ How Celery Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DJANGO WEB SERVER                         │
│                 (Handles HTTP Requests)                      │
│                                                              │
│  def book_ticket(request):                                   │
│      # Do critical work now                                  │
│      booking = create_booking()                              │
│                                                              │
│      # Queue background work                                 │
│      send_email.delay(booking.id)  ──────┐                  │
│                                           │                  │
│      return "Success!"                    │                  │
└───────────────────────────────────────────┼──────────────────┘
                                            │
                                            ▼
                              ┌──────────────────────┐
                              │   MESSAGE BROKER     │
                              │      (Redis)         │
                              │                      │
                              │  Queue of Tasks:     │
                              │  1. Send email #123  │
                              │  2. Send SMS #124    │
                              │  3. Expire bookings  │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │   CELERY WORKER      │
                              │   (Background Job)   │
                              │                      │
                              │  1. Take task from   │
                              │     queue            │
                              │  2. Execute it       │
                              │  3. Mark as done     │
                              │  4. Repeat forever   │
                              └──────────────────────┘
```

### Components

#### 1. **Django Web Server** (Main Application)
- Handles user requests (booking tickets, viewing movies)
- Queues tasks to Celery (sends email, cleanup)
- Responds to users immediately

#### 2. **Redis** (Message Broker)
- Acts as a "to-do list" for Celery
- Stores tasks waiting to be executed
- Like a queue at the DMV - first in, first out

#### 3. **Celery Worker** (Background Processor)
- Runs as a separate process
- Picks up tasks from Redis queue
- Executes them one by one
- Can have multiple workers running in parallel

#### 4. **Celery Beat** (Scheduler)
- Like a cron job
- Runs tasks on a schedule (every minute, every hour, etc.)
- Example: Clean up expired bookings every 60 seconds

---

## 🎬 Celery in Our System

### Our Celery Tasks

We have two main types of tasks:

#### 1. **On-Demand Tasks** (Triggered by User Actions)
```python
# File: bookings/email_utils.py

@shared_task
def send_booking_confirmation_email(booking_id):
    """
    Send confirmation email after successful booking.
    Called immediately after payment succeeds.
    """
    booking = Booking.objects.get(id=booking_id)
    
    send_mail(
        subject=f'Booking Confirmed - {booking.booking_number}',
        message=f'Your seats {booking.seats} are confirmed!',
        from_email='noreply@moviebooking.com',
        recipient_list=[booking.user.email],
    )
    
    return f"Email sent to {booking.user.email}"
```

**When it runs:** Immediately after user completes payment
**Why async:** Email servers can be slow, don't make user wait

#### 2. **Scheduled Tasks** (Run Periodically)
```python
# File: bookings/tasks.py

@shared_task
def release_expired_bookings():
    """
    Find and expire all PENDING bookings past their expiry time.
    Runs automatically every 60 seconds via Celery Beat.
    """
    expired_bookings = Booking.objects.filter(
        status='PENDING',
        expires_at__lt=timezone.now()
    )
    
    released_count = 0
    for booking in expired_bookings:
        # Expire booking and release seats
        success, error = BookingService.expire_booking(booking)
        if success:
            released_count += 1
            logger.info(f"Expired: {booking.booking_number}")
    
    return f"Released {released_count} expired bookings"
```

**When it runs:** Every 60 seconds, automatically
**Why needed:** Catches bookings that users abandoned

---

## 🎭 Real-World Example

Let's follow a complete booking flow with Celery:

### Scenario: John Books Seats A1, A2

#### **Step 1: User Makes Booking (6:00 PM)**
```python
# File: bookings/views.py

def create_booking(request):
    # 1. Reserve seats in Redis (instant)
    SeatManager.reserve_seats(showtime_id, ['A1', 'A2'], user.id)
    
    # 2. Create booking in database (fast)
    booking = Booking.objects.create(
        user=user,
        showtime=showtime,
        seats=['A1', 'A2'],
        status='PENDING',
        expires_at=now() + timedelta(minutes=10)  # 6:10 PM
    )
    
    # 3. User sees response immediately
    return redirect('payment_page', booking.id)
    
    # Total time: ~2 seconds ✅
```

#### **Step 2: User Completes Payment (6:05 PM)**
```python
# File: bookings/views.py

def payment_success(request, booking_id):
    # 1. Confirm booking (instant)
    booking.status = 'CONFIRMED'
    booking.save()
    
    # 2. Queue email task (instant, doesn't wait!)
    send_booking_confirmation_email.delay(booking_id)
    #                               ^^^^^ 
    #                          This makes it async!
    
    # 3. Queue SMS task (instant)
    send_booking_sms.delay(booking_id)
    
    # 4. User sees success page immediately
    return render('booking_success.html')
    
    # Total time: ~1 second ✅
    # Email sends in background (user doesn't wait)
```

**What happens behind the scenes:**
```
6:05:00 PM - Django: Queue email task to Redis
6:05:00 PM - Django: Queue SMS task to Redis
6:05:00 PM - Django: Show success page to user ✅

[Background - Celery Worker picks up tasks]
6:05:02 PM - Celery: Start sending email...
6:05:07 PM - Celery: Email sent ✅
6:05:07 PM - Celery: Start sending SMS...
6:05:10 PM - Celery: SMS sent ✅

[User already moved on, doesn't care about delays]
```

#### **Step 3: Alternative - User Abandons Payment**
```python
# User closes browser at 6:05 PM, never completes payment
# Booking stays as PENDING with expires_at = 6:10 PM

# Meanwhile, Celery Beat is running...

# 6:06 PM - Celery Beat: Check for expired bookings
# (No expired bookings yet, expires_at is 6:10 PM)

# 6:07 PM - Celery Beat: Check again
# (Still no expired bookings)

# 6:11 PM - Celery Beat: Check again
@shared_task
def release_expired_bookings():
    expired = Booking.objects.filter(
        status='PENDING',
        expires_at__lt=timezone.now()  # 6:11 PM
    )
    # Found: John's booking (expires_at = 6:10 PM) ✅
    
    for booking in expired:
        # Change status to EXPIRED
        booking.status = 'EXPIRED'
        booking.save()
        
        # Release seats in Redis
        SeatManager.release_seats(
            booking.showtime.id,
            booking.seats,
            user_id=booking.user.id
        )
        # A1 and A2 now available again! ✅
    
    return "Released 1 expired bookings"
```

**Timeline:**
```
6:00 PM - Booking created (PENDING, expires 6:10 PM)
6:05 PM - User abandons payment, closes browser
6:10 PM - Booking expires (passes expires_at time)
6:11 PM - Celery Beat runs cleanup task
6:11 PM - Booking marked EXPIRED, seats released ✅
```

---

## ⏰ Celery Beat (Scheduler)

**Celery Beat** is like a smart alarm clock that triggers tasks on a schedule.

### Configuration
```python
# File: moviebooking/celery.py

from celery import Celery
from celery.schedules import crontab

app = Celery('moviebooking')

# Schedule periodic tasks
app.conf.beat_schedule = {
    # Task 1: Release expired bookings every 60 seconds
    'release-expired-bookings': {
        'task': 'bookings.tasks.release_expired_bookings',
        'schedule': 60.0,  # Run every 60 seconds
    },
    
    # Task 2: Send reminder emails every day at 6 AM
    'send-showtime-reminders': {
        'task': 'bookings.tasks.send_showtime_reminders',
        'schedule': crontab(hour=6, minute=0),  # 6:00 AM daily
    },
    
    # Task 3: Clean old data every Sunday at midnight
    'cleanup-old-data': {
        'task': 'bookings.tasks.cleanup_old_data',
        'schedule': crontab(day_of_week=0, hour=0, minute=0),
    },
}
```

### Schedule Types

#### 1. **Simple Interval** (Every X Seconds)
```python
'schedule': 60.0  # Every 60 seconds
'schedule': 300.0  # Every 5 minutes
'schedule': 3600.0  # Every hour
```

#### 2. **Cron Expression** (Specific Times)
```python
# Every day at 9 AM
'schedule': crontab(hour=9, minute=0)

# Every Monday at 6 PM
'schedule': crontab(day_of_week=1, hour=18, minute=0)

# Every hour at minute 30
'schedule': crontab(minute=30)

# First day of month at midnight
'schedule': crontab(day_of_month=1, hour=0, minute=0)
```

---

## 📋 Common Celery Tasks

### 1. **Send Confirmation Email** (On-Demand)
```python
@shared_task
def send_booking_confirmation_email(booking_id):
    """Runs after payment success"""
    booking = Booking.objects.get(id=booking_id)
    # Send email...
    return f"Email sent for {booking.booking_number}"

# Usage in views.py:
send_booking_confirmation_email.delay(booking.id)
```

### 2. **Release Expired Bookings** (Scheduled)
```python
@shared_task
def release_expired_bookings():
    """Runs every 60 seconds automatically"""
    expired = Booking.objects.filter(
        status='PENDING',
        expires_at__lt=timezone.now()
    )
    
    for booking in expired:
        BookingService.expire_booking(booking)
    
    return f"Released {expired.count()} bookings"

# Scheduled in celery.py (runs automatically)
```

### 3. **Send Reminder Notifications** (Scheduled)
```python
@shared_task
def send_showtime_reminders():
    """Runs daily at 6 AM"""
    # Find bookings for shows in next 2 hours
    upcoming = Booking.objects.filter(
        status='CONFIRMED',
        showtime__start_time__range=[
            timezone.now(),
            timezone.now() + timedelta(hours=2)
        ]
    )
    
    for booking in upcoming:
        send_email(booking.user.email, "Show starts in 2 hours!")
    
    return f"Sent {upcoming.count()} reminders"
```

### 4. **Generate Reports** (Scheduled)
```python
@shared_task
def generate_daily_report():
    """Runs every day at midnight"""
    today = timezone.now().date()
    
    bookings = Booking.objects.filter(
        confirmed_at__date=today
    )
    
    report = {
        'total_bookings': bookings.count(),
        'total_revenue': sum(b.total_amount for b in bookings),
        'most_popular_movie': ...
    }
    
    # Email report to admin
    send_mail('Daily Report', report, 'admin@moviebooking.com')
    
    return "Report generated"
```

---

## 🚀 Running Celery

### Start Celery Worker
```bash
# Terminal 1: Start worker (processes tasks)
celery -A moviebooking worker --loglevel=info

# Output:
# [2026-01-03 18:00:00] celery@MacBook-Pro ready
# [2026-01-03 18:00:05] Task bookings.tasks.send_email[abc123] received
# [2026-01-03 18:00:10] Task bookings.tasks.send_email[abc123] succeeded
```

### Start Celery Beat
```bash
# Terminal 2: Start beat (scheduler)
celery -A moviebooking beat --loglevel=info

# Output:
# [2026-01-03 18:00:00] Scheduler: Sending due task release-expired-bookings
# [2026-01-03 18:01:00] Scheduler: Sending due task release-expired-bookings
# [2026-01-03 18:02:00] Scheduler: Sending due task release-expired-bookings
```

### Monitor Tasks
```bash
# Terminal 3: Monitor Celery events
celery -A moviebooking events

# Or use Flower (web-based monitoring)
pip install flower
celery -A moviebooking flower
# Open: http://localhost:5555
```

---

## 🔧 Troubleshooting

### Problem 1: Tasks Not Executing
```bash
# Check if worker is running
ps aux | grep celery

# If not running, start it
celery -A moviebooking worker --loglevel=info

# Check Redis connection
redis-cli ping
# Should return: PONG
```

### Problem 2: Scheduled Tasks Not Running
```bash
# Check if Celery Beat is running
ps aux | grep "celery beat"

# If not running, start it
celery -A moviebooking beat --loglevel=info

# Check beat schedule
python manage.py shell
>>> from moviebooking.celery import app
>>> print(app.conf.beat_schedule)
```

### Problem 3: Tasks Failing Silently
```python
# Add error handling to tasks
@shared_task(bind=True)
def send_email(self, booking_id):
    try:
        # Task code...
        pass
    except Exception as exc:
        # Log error
        logger.error(f"Task failed: {exc}")
        # Retry after 5 minutes
        raise self.retry(exc=exc, countdown=300)
```

### Problem 4: Too Many Tasks Queued
```bash
# Check queue length
redis-cli
> LLEN celery

# If too many, purge queue (DANGEROUS!)
celery -A moviebooking purge

# Or add more workers
celery -A moviebooking worker --concurrency=4
```

---

## 📊 Celery vs Regular Code

| Feature | Regular Code | Celery Task |
|---------|-------------|-------------|
| **Execution** | Immediate | Background |
| **User Waits** | Yes ⏳ | No ✅ |
| **Failure Handling** | Blocks everything | Can retry |
| **Scalability** | Limited | Unlimited workers |
| **Scheduling** | Manual cron | Built-in Beat |
| **Monitoring** | Basic logs | Flower dashboard |

---

## 🎓 Key Takeaways

1. **Celery = Background Worker**: Does slow work without blocking users
2. **Beat = Scheduler**: Runs tasks automatically on a schedule
3. **Redis = Message Queue**: Stores tasks waiting to be executed
4. **Async = Better UX**: Users see results immediately
5. **Retry = Fault Tolerance**: Failed tasks can retry automatically
6. **Monitoring = Essential**: Use Flower to watch task execution

---

## 🚀 Next Steps

1. Read: [Understanding Redis](./UNDERSTANDING_REDIS.md) - Learn about the message broker
2. Read: [Understanding Razorpay](./UNDERSTANDING_RAZORPAY.md) - Learn about payments
3. Practice: Create a simple task and watch it execute
4. Experiment: Try different schedules for periodic tasks

---

**Remember**: Celery is like hiring assistants - they do the slow work in the background while you focus on serving customers! 🎯⚙️

*Last Updated: January 3, 2026*
