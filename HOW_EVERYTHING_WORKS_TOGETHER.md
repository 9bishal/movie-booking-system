# 🎬 How Redis, Celery, and Razorpay Work Together
## Complete System Integration Guide

---

## 📚 Table of Contents
1. [The Big Picture](#the-big-picture)
2. [Complete Booking Flow](#complete-booking-flow)
3. [Role of Each Component](#role-of-each-component)
4. [Timeline Example](#timeline-example)
5. [What Happens When...](#what-happens-when)
6. [Quick Reference](#quick-reference)

---

## 🎯 The Big Picture

Think of our movie booking system as a **restaurant**:

| Component | Restaurant Analogy | Real System |
|-----------|-------------------|-------------|
| **Django** | Waiter (takes orders) | Web server (handles requests) |
| **Redis** | Order pad (temporary notes) | Cache (seat reservations) |
| **Database** | Kitchen records (permanent) | PostgreSQL (confirmed bookings) |
| **Razorpay** | Payment terminal | Payment gateway |
| **Celery Worker** | Kitchen staff (cooks food) | Background tasks (emails, cleanup) |
| **Celery Beat** | Timer (reminds to clean) | Scheduler (periodic tasks) |

### System Architecture

```
                    ┌─────────────────────┐
                    │       USER          │
                    │  (Web Browser)      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   DJANGO SERVER     │
                    │  (Main Application) │
                    └─────┬──────┬────────┘
                          │      │
        ┌─────────────────┘      └─────────────────┐
        │                                           │
        ▼                                           ▼
┌───────────────┐                         ┌────────────────┐
│     REDIS     │                         │   RAZORPAY     │
│   (CACHE)     │                         │   (PAYMENT)    │
├───────────────┤                         ├────────────────┤
│ • Seat locks  │                         │ • Orders       │
│ • Reservations│                         │ • Payments     │
│ • Sessions    │                         │ • Refunds      │
│               │                         │                │
│ Auto-expires  │                         │ Secure & PCI   │
│ (10 minutes)  │                         │ compliant      │
└───────┬───────┘                         └────────────────┘
        │
        │ (Task Queue)
        ▼
┌───────────────────────────────────────────────────────────┐
│              CELERY (Background Workers)                  │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  CELERY WORKER              CELERY BEAT                   │
│  (Does tasks)               (Scheduler)                   │
│  ├─ Send emails             ├─ Every 60s:                │
│  ├─ Generate reports        │   └─ Expire bookings       │
│  └─ Process refunds         ├─ Every day 6 AM:           │
│                             │   └─ Send reminders        │
│                             └─ Every Sunday:              │
│                                 └─ Cleanup old data       │
└───────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────┐
│   DATABASE    │
│ (PostgreSQL)  │
├───────────────┤
│ • Users       │
│ • Movies      │
│ • Bookings    │
│ • Payments    │
│               │
│ Permanent     │
│ storage       │
└───────────────┘
```

---

## 🎭 Complete Booking Flow

Let's follow John booking tickets step-by-step:

### Phase 1: Seat Selection (0-30 seconds)

```
USER ACTION: John clicks seats A1, A2
     ↓
DJANGO: receive_seat_selection()
     ├─→ Check Redis: Are seats available?
     │   └─→ REDIS GET: reserved_seats_24
     │       Returns: [] (empty, seats free!)
     │
     ├─→ Reserve in Redis (10-minute lock)
     │   └─→ REDIS SETEX: seat_lock:24:A1 = user_7, TTL=600
     │   └─→ REDIS SETEX: seat_lock:24:A2 = user_7, TTL=600
     │   └─→ REDIS SET: reserved_seats_24 = ['A1', 'A2'], TTL=600
     │   └─→ REDIS SET: seat_reservation_24_7 = {...}, TTL=600
     │
     └─→ Create PENDING booking in database
         └─→ DATABASE INSERT: Booking(status=PENDING, expires_at=now+10min)

USER RESULT: "Seats reserved! Complete payment in 10 minutes"
```

**State After Phase 1:**
```
Redis:
  ✅ seat_lock:24:A1 = "7" (expires in 10 min)
  ✅ seat_lock:24:A2 = "7" (expires in 10 min)
  ✅ reserved_seats_24 = ["A1", "A2"]
  ✅ seat_reservation_24_7 = {...}

Database:
  ✅ Booking #12345 (PENDING, expires_at: 6:10 PM)

Celery:
  ⏳ (No tasks yet)

Razorpay:
  ⏳ (No order yet)
```

---

### Phase 2: Payment Page (30 seconds - 2 minutes)

```
USER ACTION: John clicks "Proceed to Payment"
     ↓
DJANGO: payment_page()
     ├─→ Get booking from database
     │   └─→ DATABASE SELECT: Booking #12345
     │
     ├─→ Check if booking is still valid
     │   ├─→ Is status PENDING? ✅
     │   ├─→ Has expired? (check expires_at) ✅ Not yet
     │   └─→ Are seats still reserved in Redis? ✅ Yes
     │
     ├─→ Create Razorpay order (or reuse if exists)
     │   └─→ RAZORPAY API: Create order
     │       Request: {amount: 50000, receipt: "booking_12345"}
     │       Response: {order_id: "order_MfL8Dxyz123"}
     │
     ├─→ Save order_id to booking
     │   └─→ DATABASE UPDATE: Booking.razorpay_order_id = "order_MfL8Dxyz123"
     │
     └─→ Show payment page with Razorpay modal

USER RESULT: Razorpay checkout modal appears
```

**State After Phase 2:**
```
Redis:
  ✅ (Same as Phase 1, still holding seats)

Database:
  ✅ Booking #12345 (PENDING, order_id: "order_MfL8Dxyz123")

Celery:
  ⏳ (No tasks yet)

Razorpay:
  ✅ Order created: "order_MfL8Dxyz123" (status: created)
```

---

### Phase 3A: Successful Payment (2-5 minutes)

```
USER ACTION: John enters card, clicks "Pay ₹500"
     ↓
RAZORPAY: Process payment
     ├─→ Validate card with bank
     ├─→ Charge card
     ├─→ Generate payment_id: "pay_MfL8EABCD456"
     └─→ Return success to browser
         {
           payment_id: "pay_MfL8EABCD456",
           order_id: "order_MfL8Dxyz123",
           signature: "a1b2c3d4..."
         }
     ↓
BROWSER: Call verify_payment()
     └─→ POST /verify_payment/ with payment details
     ↓
DJANGO: verify_payment()
     ├─→ Verify signature (CRITICAL security check!)
     │   └─→ HMAC-SHA256(order_id|payment_id, secret_key)
     │       Expected: "a1b2c3d4..."
     │       Received: "a1b2c3d4..."
     │       Match? ✅ YES → Payment is genuine!
     │
     ├─→ Find booking by order_id
     │   └─→ DATABASE SELECT: Booking with razorpay_order_id="order_MfL8Dxyz123"
     │
     ├─→ Confirm booking
     │   └─→ DATABASE UPDATE: 
     │       Booking.status = "CONFIRMED"
     │       Booking.payment_id = "pay_MfL8EABCD456"
     │       Booking.confirmed_at = now()
     │
     ├─→ Release Redis locks (seats now permanently booked)
     │   └─→ REDIS DELETE: seat_lock:24:A1
     │   └─→ REDIS DELETE: seat_lock:24:A2
     │   └─→ REDIS DELETE: seat_reservation_24_7
     │   └─→ REDIS UPDATE: reserved_seats_24 = [] (or keep for history)
     │
     ├─→ Queue confirmation email (async!)
     │   └─→ CELERY: send_booking_confirmation_email.delay(booking_id)
     │       └─→ REDIS LPUSH: celery (task queue)
     │           Task: {
     │               task: "send_booking_confirmation_email",
     │               args: [12345]
     │           }
     │
     └─→ Return success to browser

     ↓
CELERY WORKER: (picks up task from queue)
     ├─→ REDIS RPOP: celery (get task from queue)
     ├─→ Execute: send_booking_confirmation_email(12345)
     │   ├─→ DATABASE SELECT: Booking #12345
     │   ├─→ Send email via SMTP
     │   └─→ Mark task as done
     │
     └─→ Wait for next task...

USER RESULT: "Booking confirmed! Check your email."
```

**Final State (Success):**
```
Redis:
  ❌ seat_lock:24:A1 = DELETED
  ❌ seat_lock:24:A2 = DELETED
  ❌ seat_reservation_24_7 = DELETED
  ✅ reserved_seats_24 = [] (cleared)

Database:
  ✅ Booking #12345 (CONFIRMED, payment_id: "pay_MfL8EABCD456")

Celery:
  ✅ Email sent successfully

Razorpay:
  ✅ Payment captured: "pay_MfL8EABCD456" (₹500 received)
```

---

### Phase 3B: Abandoned Payment (User Closes Browser)

```
USER ACTION: John closes browser at 6:05 PM
     ↓
SYSTEM: Booking stays PENDING (expires_at: 6:10 PM)
     ↓
REDIS: Auto-expires locks at 6:10 PM
     └─→ TTL countdown: 600 → 599 → 598 → ... → 1 → 0
     └─→ At TTL=0: REDIS AUTO-DELETE all keys
         ❌ seat_lock:24:A1
         ❌ seat_lock:24:A2
         ❌ reserved_seats_24
         ❌ seat_reservation_24_7
     ↓
CELERY BEAT: (runs every 60 seconds)
     6:06:00 PM → Check for expired bookings
                  └─→ DATABASE SELECT: Bookings where expires_at < now()
                      Result: None (expires_at is 6:10 PM)
                      
     6:07:00 PM → Check again
                  └─→ Result: None
                  
     6:08:00 PM → Check again
                  └─→ Result: None
                  
     6:11:00 PM → Check again
                  └─→ Result: Found Booking #12345! (expires_at: 6:10 PM < 6:11 PM)
                  ↓
CELERY WORKER: release_expired_bookings()
     ├─→ Found 1 expired booking
     ├─→ For Booking #12345:
     │   ├─→ DATABASE UPDATE: status = "EXPIRED"
     │   ├─→ REDIS DELETE: seat_lock:24:A1 (already deleted by TTL)
     │   ├─→ REDIS DELETE: seat_lock:24:A2 (already deleted by TTL)
     │   └─→ REDIS DELETE: seat_reservation_24_7 (already deleted by TTL)
     │
     └─→ Log: "Released 1 expired bookings"

RESULT: Seats A1, A2 now available for others! ✅
```

**Final State (Abandoned):**
```
Redis:
  ❌ All keys deleted (by TTL or Celery cleanup)

Database:
  ✅ Booking #12345 (EXPIRED)

Celery:
  ✅ Cleanup task completed

Razorpay:
  ✅ Order still exists but never paid
```

---

## 🔄 Role of Each Component

### Django (The Conductor)
**What it does:**
- Receives user requests
- Validates input
- Coordinates between Redis, Database, Razorpay, Celery
- Returns responses to user

**When it's involved:**
- Every user action (click, submit form, etc.)
- API calls from frontend
- Initial request handling

**Example:**
```python
def book_ticket(request):
    # 1. Validate request
    # 2. Check Redis (are seats free?)
    # 3. Create booking in database
    # 4. Create Razorpay order
    # 5. Queue Celery task
    # 6. Return response
    pass
```

---

### Redis (The Notepad)
**What it does:**
- Temporarily holds seat reservations (10 min)
- Stores Celery task queue
- Caches frequently accessed data
- Auto-deletes expired data

**When it's involved:**
- Every seat selection (lock seats)
- Every payment (check if still reserved)
- Every Celery task (queue storage)
- Every 10 minutes (auto-cleanup)

**Example:**
```
User selects A1 → REDIS: "Lock A1 for user_7, delete after 10 min"
10 minutes pass → REDIS: "TTL=0, delete A1 lock" (automatic!)
```

---

### Database (The Filing Cabinet)
**What it does:**
- Permanently stores all data
- Records bookings, users, movies
- Never auto-deletes (unless you tell it to)
- Slow but reliable

**When it's involved:**
- Creating bookings
- Confirming payments
- Looking up user history
- Generating reports

**Example:**
```python
# Write to database (permanent)
booking = Booking.objects.create(...)  # Saved forever

# Write to Redis (temporary)
cache.setex('seat_A1', 600, user_id)  # Gone after 10 min
```

---

### Razorpay (The Cash Register)
**What it does:**
- Handles payment processing
- Securely collects card details
- Charges cards, processes refunds
- Returns payment confirmation

**When it's involved:**
- When user clicks "Pay Now"
- When payment succeeds/fails
- When refund is needed

**Example:**
```
User clicks Pay → Razorpay modal opens
User enters card → Razorpay charges card
Payment success → Razorpay returns payment_id
```

---

### Celery Worker (The Kitchen Staff)
**What it does:**
- Executes background tasks
- Sends emails, generates reports
- Processes refunds
- Doesn't block user requests

**When it's involved:**
- After payment success (send email)
- When report is needed (generate PDF)
- When refund requested (process refund)

**Example:**
```
User completes payment → Django queues email task
User sees success page immediately (doesn't wait for email)
Meanwhile, Celery sends email in background (5 seconds later)
```

---

### Celery Beat (The Alarm Clock)
**What it does:**
- Schedules periodic tasks
- Triggers Celery workers at set times
- Runs every X seconds/minutes/hours

**When it's involved:**
- Every 60 seconds (expire bookings)
- Every day at 6 AM (send reminders)
- Every Sunday (cleanup old data)

**Example:**
```
6:00 PM → Check for expired bookings (none found)
6:01 PM → Check for expired bookings (none found)
6:02 PM → Check for expired bookings (found 1!)
         → Celery Worker: Expire that booking
```

---

## ⏰ Timeline Example

Complete 15-minute timeline of John's booking:

```
6:00:00 PM - John lands on movie page
           - Django: Load movie details from DATABASE
           - Shows available seats (checks REDIS)

6:01:30 PM - John selects seats A1, A2
           - Django: Lock seats in REDIS (10-min TTL)
           - Django: Create booking in DATABASE (PENDING)
           - Response time: 200ms ✅

6:02:00 PM - John clicks "Proceed to Payment"
           - Django: Create RAZORPAY order
           - Django: Show payment page
           - Response time: 500ms ✅

6:03:00 PM - John sees Razorpay modal
           - RAZORPAY: Show payment form
           - John enters card details...

6:05:00 PM - John clicks "Pay ₹500"
           - RAZORPAY: Process payment (2 seconds)
           - RAZORPAY: Return payment_id
           - Browser: Call Django /verify_payment/

6:05:02 PM - Django receives payment confirmation
           - Django: Verify signature ✅
           - Django: Update DATABASE (CONFIRMED)
           - Django: Clear REDIS locks
           - Django: Queue CELERY task (send email)
           - Response time: 300ms ✅

6:05:03 PM - John sees "Booking Confirmed!" page
           - Total time from click to confirmation: 3 seconds ✅

6:05:05 PM - CELERY WORKER picks up email task
           - Celery: Send confirmation email
           - Task duration: 2 seconds ✅

6:05:07 PM - John receives email ✅

[Meanwhile, Celery Beat is running every minute...]

6:06:00 PM - CELERY BEAT: Check expired bookings (none)
6:07:00 PM - CELERY BEAT: Check expired bookings (none)
6:08:00 PM - CELERY BEAT: Check expired bookings (none)
...

6:11:30 PM - REDIS: Auto-expire old seat locks (TTL=0)
           - Locks from 6:01:30 PM are now gone
```

---

## 💡 What Happens When...

### ❓ User Refreshes Payment Page?
```
1. Frontend JS detects refresh (sessionStorage check)
2. Frontend calls /api/cancel_booking/
3. Django calls BookingService.force_expire_booking()
4. Django updates DATABASE (EXPIRED)
5. Django clears REDIS (all keys deleted)
6. Frontend shows error page with "Start New Booking" button
```

### ❓ User Closes Razorpay Modal?
```
1. Razorpay fires ondismiss event
2. Frontend JS calls /api/cancel_booking/
3. (Same as refresh - expire and cleanup)
```

### ❓ 10-Minute Timer Expires?
```
1. Frontend countdown reaches 0
2. Frontend calls /api/cancel_booking/
3. (Same as refresh - expire and cleanup)
```

### ❓ User Abandons Payment and Closes Browser?
```
1. Redis TTL expires (after 10 min) → Auto-delete locks
2. Celery Beat runs (every 60s) → Find expired booking
3. Celery Worker expires booking → Update database
4. Result: Seats released, available for others
```

### ❓ Payment Succeeds?
```
1. Razorpay charges card
2. Django verifies signature
3. Django confirms booking in DATABASE
4. Django clears REDIS locks
5. Django queues CELERY email task
6. Celery sends confirmation email
7. User sees success page
```

### ❓ Payment Fails?
```
1. Razorpay returns error
2. Django shows error message
3. Redis keeps locks (user can retry within 10 min)
4. If user doesn't retry, Celery expires booking after 10 min
```

### ❓ Email Sending Fails?
```
1. Celery tries to send email
2. SMTP server returns error
3. Celery retries after 5 minutes (configured retry)
4. If still fails, logs error but booking stays confirmed
5. Admin can manually resend email
```

### ❓ Redis Crashes?
```
1. All seat locks lost (not persistent)
2. Django falls back to database checks
3. Slower but functional
4. Restart Redis → Empty cache → Rebuild from database
```

### ❓ Celery Worker Crashes?
```
1. Tasks stay in queue (Redis)
2. Restart worker → Pick up queued tasks
3. Email sending might be delayed but not lost
4. Expiry task might miss one cycle but catch up next run
```

### ❓ Database is Down?
```
1. System can't function (critical dependency)
2. All requests fail
3. Redis locks stay (temporary data)
4. Restart database → System resumes
```

---

## 📋 Quick Reference

### When to Use What

| Task | Use | Why |
|------|-----|-----|
| Check seat availability | Redis | Fast, temporary locks |
| Store confirmed booking | Database | Permanent record |
| Process payment | Razorpay | Secure, PCI compliant |
| Send email | Celery | Async, don't block user |
| Expire old bookings | Celery Beat | Scheduled cleanup |
| Lock seat for 10 min | Redis TTL | Auto-expires |
| Store user password | Database | Permanent, secure |
| Queue task | Redis (Celery) | Fast message broker |

### Component Comparison

| Feature | Redis | Database | Razorpay | Celery |
|---------|-------|----------|----------|--------|
| **Speed** | ⚡ Instant | 🐌 Slow | 🚀 Fast | 🏃 Background |
| **Persistence** | ⏳ Temporary | 💾 Permanent | 💾 Permanent | ⏳ Task queue |
| **Auto-Delete** | ✅ Yes (TTL) | ❌ No | ❌ No | ✅ Yes (after task) |
| **Use For** | Caching, locks | Main data | Payments | Background jobs |

---

## 🎓 Key Takeaways

1. **Django = Conductor**: Coordinates everything
2. **Redis = Notepad**: Fast, temporary, self-cleaning
3. **Database = Filing Cabinet**: Slow, permanent, reliable
4. **Razorpay = Cash Register**: Secure payment processing
5. **Celery Worker = Kitchen**: Does slow work in background
6. **Celery Beat = Timer**: Runs scheduled tasks

**Together they create a fast, reliable, secure booking system!** 🎉

---

## 🚀 Next Steps

1. Read: [Understanding Redis](./UNDERSTANDING_REDIS.md) - Deep dive into caching
2. Read: [Understanding Celery](./UNDERSTANDING_CELERY.md) - Deep dive into background tasks
3. Read: [Understanding Razorpay](./UNDERSTANDING_RAZORPAY.md) - Deep dive into payments
4. Practice: Watch system logs during a booking to see all components in action

---

**Remember**: Each component has a specific job. Don't use a screwdriver to hammer nails - use the right tool for each task! 🛠️

*Last Updated: January 3, 2026*
