# 🎬 MOVIE BOOKING SYSTEM: COMPLETE UNDERSTANDING GUIDE

**Purpose**: Understand how everything works together in ONE document

---

## 🎯 SYSTEM AT A GLANCE

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER (Front-end)                             │
│                  Web Browser / Mobile App                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ HTTP Requests
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              DJANGO WEB SERVER (views.py)                       │
│  ├─ select_seats → Show interactive seat map                   │
│  ├─ reserve_seats (AJAX) → Lock seats in Redis                 │
│  ├─ create_booking → Save PENDING booking to DB                │
│  ├─ payment_success → Verify payment, mark CONFIRMED           │
│  ├─ payment_failed → Mark FAILED, send failure email           │
│  └─ razorpay_webhook → Backup payment confirmation             │
└──────────────┬──────────────────────────────────────┬───────────┘
               │                                      │
        Reads/Writes                            Sends async
        SQL Data                                task to broker
               │                                      │
               ▼                                      ▼
    ┌──────────────────┐              ┌──────────────────────┐
    │ PostgreSQL DB    │              │  Redis Broker        │
    │ ├─ Users         │              │  (Message Queue)     │
    │ ├─ Movies        │              │                      │
    │ ├─ Bookings      │              │  Stores:             │
    │ ├─ Payments      │              │  ├─ Pending emails   │
    │ └─ Seats         │              │  ├─ Seat reservations│
    └──────────────────┘              │  └─ Cached data      │
                                       └────────┬─────────────┘
                                               │
                                          Pulls tasks
                                               │
                                               ▼
                           ┌──────────────────────────────┐
                           │  Celery Workers (Background) │
                           │  ├─ Email sender             │
                           │  ├─ Seat releaser            │
                           │  ├─ PDF generator            │
                           │  └─ Cleanup tasks            │
                           └──────────────────────────────┘
```

---

## 📋 SYSTEM COMPONENTS EXPLAINED

### 1. Frontend (Browser)
**What it does**: Shows UI to users
**Technologies**: HTML, CSS, JavaScript, Bootstrap

**Key Pages**:
- Homepage: Browse movies
- Movie detail: See trailers, ratings
- Seat selection: Interactive map
- Payment: Razorpay modal
- Booking confirmation: Digital ticket

---

### 2. Django Backend (Web Server)
**What it does**: Processes requests, handles business logic

**Responsibilities**:
- Authentication (Login/Register/Logout)
- Movie & Theater management
- Booking workflow
- Payment processing
- Email triggering
- Rate limiting

**Key Files**:
- `bookings/views.py` - Booking & payment logic
- `movies/models.py` - Movie data structure
- `movies/views.py` - Movie listing & detail
- `accounts/views.py` - User authentication
- `dashboard/views.py` - Admin analytics

---

### 3. PostgreSQL Database
**What it does**: Permanently stores data

**Key Tables**:
```
users              → User accounts, email, password
movies             → Movie info (title, description, rating)
theaters           → Theater locations
screens            → Screens within theaters
showtimes          → Movie + Screen + Time
bookings           → Booking records (status: PENDING/CONFIRMED/FAILED)
transactions       → Payment records
seats              → Individual seat data
```

**Data Flow**:
1. User registers → Creates user record
2. User selects seats → Creates booking record
3. User completes payment → Updates booking to CONFIRMED
4. Booking expires → Celery updates to FAILED

---

### 4. Redis Cache (Fast Storage)
**What it does**: Temporarily stores frequently accessed data

**Key Use Cases**:

1. **Seat Reservation** (Most critical)
```
Key: seat_reservation_1_user_5
Value: ["A1", "A2", "A3"]
TTL: 12 minutes (auto-delete after expiry)

What happens:
- User selects seat A1 → Redis key created
- 10 minutes pass → Still locked (other users can't book)
- User pays → Redis key deleted (seats confirmed)
- 12 minutes pass → Redis auto-deletes (if user abandoned)
```

2. **Caching** (Performance)
```
Key: movie_list
Value: [Movie1, Movie2, ...]
TTL: 1 hour

What happens:
- First request → Load from database, cache result
- Next 59 requests → Load from Redis (fast!)
- After 1 hour → Reload from database
```

3. **Session Storage** (User state)
```
Key: session_abc123
Value: {seat_ids: ["A1", "A2"], cart_total: 500}

What happens:
- User selects seats → Stored in session
- User navigates away → Session persists
- User returns → Can see previously selected seats
```

---

### 5. Celery (Background Task Worker)
**What it does**: Processes long-running tasks without blocking users

**Key Tasks**:

1. **Email Sending** (1-2 seconds each)
```python
# Without Celery (SLOW):
send_email()  # Takes 2 seconds, user waits ❌
response = "Email sent"  # After 2 seconds

# With Celery (FAST):
send_email.delay()  # Returns immediately ✅
response = "Email queued"  # Instant!
# Background worker sends email later
```

2. **Seat Release** (Cleanup)
```
When: Every 15 minutes
What: Release seats that expired (12+ minutes old)
How: Query Redis for expired seats → Delete them
Why: So other users can book those seats
```

3. **PDF Generation** (5-10 seconds)
```
When: After booking confirmed
What: Generate PDF ticket with QR code
How: Use ReportLab to create PDF
Why: User can print or screenshot
```

---

### 6. Razorpay (Payment Gateway)
**What it does**: Processes credit card payments securely

**Flow**:
```
1. User clicks "Pay Now"
   ↓
2. Frontend shows Razorpay modal
   ↓
3. User enters card details IN RAZORPAY (not on our server)
   ↓
4. Razorpay processes payment
   ↓
5. Razorpay sends confirmation:
   - Via redirect (user sees success page)
   - Via webhook (backup notification)
   ↓
6. Our server verifies payment using secret key
   ↓
7. If valid: Mark booking CONFIRMED
   If invalid: Mark booking FAILED
```

**Safety Checks**:
- Signature verification (ensures it's really Razorpay)
- Order ID matching (ensures payment is for this booking)
- Late payment detection (reject if seat window expired)
- Duplicate prevention (don't confirm same booking twice)

---

## 🔄 COMPLETE BOOKING FLOW

### Step 1: User Logs In
```
Browser → Django → Check credentials → PostgreSQL
If valid: Create session cookie
If invalid: Redirect to login
```

### Step 2: Browse Movies
```
Browser → Django (views.py)
Django → PostgreSQL (fetch movies)
PostgreSQL → Django → Browser (display list)

Cache layer:
First request: PostgreSQL
Next 59 requests: Redis (same data)
```

### Step 3: View Showtimes
```
Browser → Django (showtime_list view)
Django → PostgreSQL (fetch showtimes)
Django → Redis (check available seats count)
Django → Browser (show showtimes with availability)
```

### Step 4: Select Seats
```
Browser → Django (select_seats view)
Django → Redis (get seat layout from cache)
Django → Redis (get reserved seats = seats locked by others)
Django → Browser (show seat map with colors):
  - Green: Available (user can click)
  - Yellow: Reserved (other user paying)
  - Red: Booked (already confirmed)
```

### Step 5: Reserve Seats (Phase 1)
```
Browser (JavaScript) → Django (reserve_seats AJAX)
Django → Session (store seat_ids)
Django → Browser (return { success: true })

What happened:
- Seats NOT locked yet (will lock in create_booking)
- Just stored intent in user's session
```

### Step 6: Review Summary
```
Browser → Django (booking_summary view)
Django → Session (retrieve selected seat_ids)
Django → PostgreSQL (get showtime details)
Django → Calculate (base + fees + taxes)
Django → Browser (show price breakdown)

User sees:
- Selected seats
- Movie details
- Theater details
- Price breakdown
- 10-minute countdown timer (for UX)
```

### Step 7: Create Booking (Phase 2)
```
Browser (JavaScript) → Django (create_booking AJAX)
Django → Redis (lock seats - Phase 2):
  - Check if still available
  - Create Redis key with TTL=12 minutes
  - If success: continue, else: error
Django → PostgreSQL (create booking record):
  - status = 'PENDING'
  - total_amount = calculated
Django → Razorpay API (create order):
  - amount
  - receipt_id
  - Razorpay returns: order_id
Django → PostgreSQL (save razorpay_order_id)
Django → Browser (return {success: true, order_id: "..."})

What happened:
- Seats now locked in Redis for 12 minutes
- Booking record created in database
- Razorpay order created (payment anchor)
```

### Step 8: Show Payment Page
```
Browser → Django (payment_page view)
Django → PostgreSQL (fetch booking)
Django → Browser (show payment landing page):
  - Movie details
  - Amount to pay
  - 10-minute countdown
  - [Pay Now] button
```

### Step 9: User Pays
```
Browser → Razorpay (modal opens)
User → Razorpay (enters card details)
Razorpay → Payment processor (Visa/Mastercard)
Razorpay → Razorpay dashboard (payment confirmed)

What happened:
- Money deducted from user's card
- Razorpay marks payment as successful
- Razorpay prepares to notify our server
```

### Step 10: Payment Confirmation
**Scenario 1: User stays on page (normal)**
```
Razorpay → Browser redirect to payment_success
Browser → Django (payment_success view):
  1. Extract razorpay_payment_id, order_id, signature
  2. Verify signature using RAZORPAY_KEY_SECRET
  3. Check order_id matches booking.razorpay_order_id
  4. Check payment_received_at is not set (duplicate guard)
  5. Check payment arrived before booking.expires_at
  6. Check seats still available (no one stole them)
  7. Set booking.status = 'CONFIRMED'
  8. Set booking.payment_received_at = now()
  9. Release Redis lock
  10. Queue email task: send_booking_confirmation_email.delay()
Django → PostgreSQL (update booking to CONFIRMED)
Django → Celery (queue email task)
Django → Browser (show success page + download ticket)
```

**Scenario 2: User closes browser (Razorpay webhook)**
```
Razorpay → Our Django (razorpay_webhook):
  1. Receive payment notification
  2. Find booking by order_id
  3. Verify payment arrived before expiration
  4. Mark booking as CONFIRMED
  5. Queue email task
  6. Return 200 OK
Django → PostgreSQL (update booking)
Django → Celery (queue email task)

Note: Will skip if payment_success already processed
      (checks if payment_received_at is set)
```

### Step 11: Email Sent (Celery Worker)
```
Celery Worker → Email task (async):
  1. Fetch booking from database
  2. Generate email content
  3. Send via SendGrid API
  4. Mark email_sent = True
  5. Done!

What user receives:
- Booking confirmation email
- Ticket details (showtime, seats, ticket #)
- Link to download PDF ticket
```

### Step 12: User Views Ticket
```
Browser → Django (booking_detail view)
Django → PostgreSQL (fetch booking)
Django → PostgreSQL (fetch showtime, movie, theater)
Django → Browser (show ticket with QR code):
  - Movie name
  - Theater name
  - Date & time
  - Seat numbers
  - Ticket ID
  - QR code (can be scanned at theater)
```

---

## 🛡️ SAFETY MECHANISMS

### 1. Seat Locking (Redis TTL)
**Problem**: User A and B select seat A1 simultaneously
**Solution**:
```
Redis SET seat_A1_user_A (TTL: 12 min)
Redis SET seat_A1_user_B → FAILS! (already locked)
User B gets error: "Seats taken by another user"
```

### 2. Payment Verification (Razorpay Signature)
**Problem**: Attacker fakes payment success response
**Solution**:
```
Razorpay sends:
  payment_id = "pay_123"
  signature = HMAC_SHA256(order_id + payment_id, SECRET_KEY)

We verify:
  Calculate expected_sig = HMAC_SHA256(order_id + payment_id, SECRET_KEY)
  If actual_sig != expected_sig: REJECT! Forged payment
```

### 3. Late Payment Detection
**Problem**: User pays 15 minutes later, seats already released
**Solution**:
```
if payment_received_at > booking.expires_at:
    booking.status = 'FAILED'
    queue refund email
    Return: "Payment window expired"
```

### 4. Duplicate Processing Prevention
**Problem**: Both webhook and payment_success view process same booking
**Solution**:
```
Set payment_received_at FIRST (atomic operation)
If payment_received_at already set: SKIP (already processed)
This blocks:
  - Duplicate confirmation emails
  - Duplicate seat confirms
  - Double-processing of payments
```

### 5. Seat Availability Check
**Problem**: Someone else booked the seats while user was paying
**Solution**:
```
After payment success:
  Query DB: SELECT * FROM bookings WHERE seat IN [...] AND status='CONFIRMED'
  If any exist: Someone else got there first!
    booking.status = 'FAILED'
    Refund initiated
    Return: "Seats taken, refund processing"
```

---

## 📊 DATABASE SCHEMA

### Users Table
```
id (PK)
username (unique)
email (unique)
password (hashed)
created_at
```

### Movies Table
```
id (PK)
title
slug (unique)
description
rating
release_date
trailer_url (YouTube)
poster_url
created_at
```

### Theaters Table
```
id (PK)
city_id (FK)
name
address
created_at
```

### Screens Table
```
id (PK)
theater_id (FK)
name
total_seats
```

### Showtimes Table
```
id (PK)
movie_id (FK)
screen_id (FK)
date
time
price
created_at
```

### Bookings Table
```
id (PK)
user_id (FK)
showtime_id (FK)
seats (JSON: ["A1", "A2"])
status (PENDING/CONFIRMED/FAILED/EXPIRED)
total_amount
base_price
convenience_fee
tax_amount
razorpay_order_id
razorpay_payment_id
payment_received_at (NULL until payment succeeds)
payment_initiated_at
expires_at (12 min from creation)
confirmed_at
created_at
```

### Transactions Table
```
id (PK)
booking_id (FK)
razorpay_payment_id
amount
status (captured/refunded/failed)
created_at
```

---

## 🔴 REDIS DATA STRUCTURES

### Seat Reservation Key
```
Key: seat_reservation_{showtime_id}_{user_id}
Value: {"A1": True, "A2": True, "A3": True}
TTL: 12 minutes

Represents: Seats locked for this user
Expires automatically: After 12 minutes
```

### Seat Layout Cache
```
Key: seat_layout_{showtime_id}
Value: [
  ["A1", "A2", "A3"],
  ["B1", "B2", "B3"],
  ...
]
TTL: 1 day

Represents: Seat grid for display
Reason: Don't recalculate every request
```

### Session Data
```
Key: session_{session_id}
Value: {
  "seat_reservation": {
    "1": ["A1", "A2"]  # showtime_id -> seat_ids
  }
}
TTL: 14 days (Django default)

Represents: User's session (includes selected seats)
```

---

## 📧 EMAIL TASKS (Celery)

### 1. Booking Confirmation Email
**When**: After payment successful
**Task**: `send_booking_confirmation_email.delay(booking_id)`
**Content**:
- Booking confirmation
- Ticket details
- Download ticket link
**Status**: Idempotent (won't send twice)

### 2. Payment Failed Email
**When**: After payment fails/cancelled
**Task**: `send_payment_failed_email.delay(booking_id)`
**Content**:
- Payment failed notice
- Seats released message
- Retry booking link
**Status**: Idempotent (won't send twice)

### 3. Late Payment Email
**When**: Payment arrives after window expired
**Task**: `send_late_payment_email.delay(booking_id)`
**Content**:
- Refund initiated notice
- Timeline (24 hours)
- Support contact
**Status**: Idempotent (won't send twice)

### 4. Showtime Reminder Email
**When**: 24 hours before showtime
**Task**: Celery Beat scheduled task
**Content**:
- Movie details
- Ticket info
- Theater directions
- Contact

---

## ⚡ PERFORMANCE OPTIMIZATIONS

### 1. Database Optimization
```
✅ Indexes on: user_id, movie_id, showtime_id, status
✅ select_related() for foreign keys
✅ prefetch_related() for reverse relations
✅ Pagination on listing pages (20 items per page)
```

### 2. Redis Caching
```
✅ Cache seat layouts (1 day)
✅ Cache movie listings (1 hour)
✅ Cache theater info (1 day)
✅ Cache user sessions (14 days)
```

### 3. Frontend Optimization
```
✅ Minify CSS/JS
✅ Lazy load images
✅ Compress images
✅ Defer non-critical JavaScript
```

### 4. API Optimization
```
✅ GZIP compression
✅ HTTP caching headers
✅ Return only necessary fields
✅ Pagination for large datasets
```

---

## 🚀 DEPLOYMENT ARCHITECTURE

### Production Stack
```
[User Browser]
     ↓
[Nginx Reverse Proxy] (Load balancer, SSL termination)
     ↓
[Gunicorn WSGI Server] × 4 workers (Django application)
     ↓
[PostgreSQL] (Data persistence)
[Redis] (Cache & Celery broker)
     ↓
[Celery Workers] × 2 (Background tasks)
[Celery Beat] × 1 (Scheduled tasks)
```

### Environment
- **Server**: Heroku / AWS EC2
- **Database**: PostgreSQL (production)
- **Cache**: Redis (production)
- **Email**: SendGrid
- **Payment**: Razorpay (live mode)
- **CDN**: CloudFlare (optional)

---

## 📈 SCALING CONSIDERATIONS

### Current Limits
```
Seat Selection: 100 concurrent users per showtime
Database: Single PostgreSQL instance
Celery: 2-4 workers for email
API Rate: 100 requests/minute per IP
```

### How to Scale
```
1. Horizontal Scaling
   - Add more Gunicorn workers
   - Add more Celery workers
   - Use load balancer (Nginx/HAProxy)

2. Database Scaling
   - Read replicas for reporting
   - Database connection pooling
   - Query optimization

3. Cache Scaling
   - Redis cluster for high availability
   - Multi-tier caching (memory + disk)

4. CDN
   - CloudFlare for static files
   - Distribute images globally
```

---

## 🆘 COMMON ISSUES & SOLUTIONS

### "Seats show as booked but user cancelled"
→ Redis key didn't expire properly
→ Solution: Run cleanup Celery task

### "Payment shows as PENDING after 15 minutes"
→ Razorpay webhook didn't fire
→ User didn't see success page
→ Solution: Check razorpay_webhook logs, manually update

### "Emails not sending"
→ SendGrid API key invalid or quota exceeded
→ Solution: Check SENDGRID_API_KEY, increase plan

### "Celery tasks stuck in queue"
→ No workers running or Redis down
→ Solution: Start Celery worker, check Redis status

### "Duplicate confirmation emails"
→ Task retried multiple times
→ Solution: Email tasks have idempotency checks, should be OK

---

## 📚 FILES TO UNDERSTAND

### High Priority (Read First)
1. `bookings/views.py` - Booking & payment workflow
2. `bookings/models.py` - Booking data structure
3. `bookings/utils.py` - SeatManager (Redis logic)
4. `bookings/email_utils.py` - Email sending

### Medium Priority
5. `movies/models.py` - Movie data structure
6. `movies/views.py` - Movie listing & detail
7. `moviebooking/settings.py` - Configuration
8. `moviebooking/celery.py` - Celery setup

### Lower Priority
9. `accounts/views.py` - Authentication
10. `dashboard/views.py` - Admin analytics
11. `bookings/tasks.py` - Celery tasks

---

## ✅ UNDERSTANDING CHECKLIST

```
After reading this document, you should understand:

Core Concepts:
[ ] How seats are locked using Redis TTL
[ ] How payments are verified using signatures
[ ] How duplicate processing is prevented
[ ] How emails are sent asynchronously

Architecture:
[ ] Role of each component (Django, PostgreSQL, Redis, Celery)
[ ] How data flows through the system
[ ] How booking moves through states

Safety:
[ ] Why signature verification matters
[ ] Why late payment detection exists
[ ] Why duplicate processing prevention is critical
[ ] Why seat availability check is needed

Deployment:
[ ] How to deploy to Heroku
[ ] What environment variables are needed
[ ] How to monitor in production
[ ] How to scale when needed
```

---

## 🎓 NEXT LEARNING STEPS

1. **Testing** (WEEK 4)
   - Write unit tests for each component
   - Test payment flow with mock Razorpay
   - Test edge cases (seat collision, late payment)

2. **Deployment** (WEEK 4)
   - Deploy to Heroku
   - Configure production settings
   - Set up monitoring

3. **Advanced Features** (AFTER WEEK 4)
   - Mobile app (React Native)
   - Advanced analytics
   - Recommendation engine
   - Multi-language support

---

**Last Updated**: 8 January 2026
**Status**: Complete Understanding Document
**Difficulty**: Beginner-Friendly
**Read Time**: 20-30 minutes

