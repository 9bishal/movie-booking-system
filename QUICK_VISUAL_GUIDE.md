# 🎯 Quick Visual Guide - Movie Booking System

A visual reference guide for understanding the system at a glance.

---

## 🏗️ System Components

```
┌─────────────────────────────────────────────────────────┐
│                    🌐 USER'S BROWSER                    │
│  • Select seats                                         │
│  • Make payment                                         │
│  • See confirmation                                     │
└────────────────────┬───────────────────────────────────┘
                     │ HTTP Requests
                     ▼
┌─────────────────────────────────────────────────────────┐
│               🎯 DJANGO WEB SERVER                      │
│  • Handle requests                                      │
│  • Business logic                                       │
│  • Coordinate components                                │
└──┬──────────────┬──────────────┬──────────────────────┘
   │              │              │
   ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌──────────────┐
│ 🗄️ REDIS   │ │ 💾 DATABASE│ │ 💳 RAZORPAY  │
│ Temp cache │ │ Permanent  │ │ Payments     │
│ 10 min TTL │ │ storage    │ │ gateway      │
└─────┬──────┘ └────────────┘ └──────────────┘
      │
      ▼
┌────────────────────────────────┐
│      ⚙️ CELERY WORKERS         │
│  • Send emails                 │
│  • Background tasks            │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│      ⏰ CELERY BEAT             │
│  • Expire bookings (60s)       │
│  • Send reminders (daily)      │
└────────────────────────────────┘
```

---

## 📊 Booking State Transitions

```
┌──────────┐    Select Seats    ┌──────────┐
│  START   │───────────────────→│ PENDING  │
│          │                     │ (10 min) │
└──────────┘                     └────┬─────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
              User Completes    User Abandons    Timer Expires
                Payment           Payment         or Refresh
                    │                 │                 │
                    ▼                 ▼                 ▼
              ┌───────────┐     ┌──────────┐    ┌──────────┐
              │ CONFIRMED │     │ CANCELLED│    │ EXPIRED  │
              │ (Permanent)│     │          │    │          │
              └───────────┘     └──────────┘    └──────────┘
```

---

## 🔄 Complete Booking Flow

```
1️⃣ USER SELECTS SEATS
    ↓
2️⃣ DJANGO → REDIS (Lock seats, 10-min TTL)
    ↓
3️⃣ DJANGO → DATABASE (Create PENDING booking)
    ↓
4️⃣ USER SEES PAYMENT PAGE
    ↓
5️⃣ DJANGO → RAZORPAY (Create order)
    ↓
6️⃣ RAZORPAY MODAL OPENS
    ↓
7️⃣ USER ENTERS CARD & PAYS
    ↓
8️⃣ RAZORPAY PROCESSES PAYMENT
    ↓
9️⃣ DJANGO VERIFIES SIGNATURE ✅
    ↓
🔟 DJANGO → DATABASE (Update to CONFIRMED)
    ↓
1️⃣1️⃣ DJANGO → REDIS (Clear locks)
    ↓
1️⃣2️⃣ DJANGO → CELERY (Queue email)
    ↓
1️⃣3️⃣ CELERY SENDS EMAIL
    ↓
1️⃣4️⃣ USER SEES SUCCESS PAGE! 🎉
```

---

## ⏰ Timeline Visualization

```
Time    | User Action           | System Response
--------|-----------------------|------------------------------------
6:00 PM | Select seats A1, A2   | Redis: Lock A1, A2 (expires 6:10)
        |                       | DB: Create booking (PENDING)
--------|-----------------------|------------------------------------
6:02 PM | Click "Pay Now"       | Razorpay: Create order
        |                       | Show payment modal
--------|-----------------------|------------------------------------
6:05 PM | Enter card, pay       | Razorpay: Process payment
        |                       | Django: Verify signature ✅
        |                       | DB: Update to CONFIRMED
        |                       | Redis: Clear locks
        |                       | Celery: Queue email
--------|-----------------------|------------------------------------
6:05 PM | See success page      | User happy! ✅
--------|-----------------------|------------------------------------
6:07 PM | -                     | Celery: Send email ✅
--------|-----------------------|------------------------------------

ALTERNATIVE TIMELINE (User Abandons):

Time    | User Action           | System Response
--------|-----------------------|------------------------------------
6:00 PM | Select seats          | Redis: Lock seats (expires 6:10)
        |                       | DB: Create booking (PENDING)
--------|-----------------------|------------------------------------
6:05 PM | Close browser ❌       | (No action)
--------|-----------------------|------------------------------------
6:10 PM | -                     | Redis: Auto-delete locks (TTL=0)
--------|-----------------------|------------------------------------
6:11 PM | -                     | Celery Beat: Find expired booking
        |                       | DB: Update to EXPIRED
        |                       | Redis: Cleanup (if any remaining)
--------|-----------------------|------------------------------------
Result  | Seats A1, A2 now available for others! ✅
```

---

## 🗄️ Redis Keys Structure

```
For Showtime ID: 24, User ID: 7, Seats: A1, A2

┌────────────────────────────────────────────────┐
│ Key: seat_lock:24:A1                           │
│ Value: "7" (user_id)                           │
│ TTL: 600 seconds (10 minutes)                  │
│ Purpose: Lock individual seat A1               │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ Key: seat_lock:24:A2                           │
│ Value: "7" (user_id)                           │
│ TTL: 600 seconds                               │
│ Purpose: Lock individual seat A2               │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ Key: reserved_seats_24                         │
│ Value: ["A1", "A2"]                            │
│ TTL: 600 seconds                               │
│ Purpose: List of all reserved seats            │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ Key: seat_reservation_24_7                     │
│ Value: {                                       │
│   "seat_ids": ["A1", "A2"],                    │
│   "reserved_at": 1767451157.5                  │
│ }                                              │
│ TTL: 600 seconds                               │
│ Purpose: User's specific reservation           │
└────────────────────────────────────────────────┘
```

---

## 💡 Decision Tree: What Component to Use?

```
Need to...

├─ Store data temporarily (< 1 hour)?
│  └─→ USE: Redis ✅
│      Examples: Seat locks, session data
│
├─ Store data permanently?
│  └─→ USE: Database ✅
│      Examples: Users, bookings, movies
│
├─ Process payment?
│  └─→ USE: Razorpay ✅
│      Example: Credit card payments
│
├─ Send email/SMS?
│  └─→ USE: Celery (async) ✅
│      Why: Don't make user wait
│
├─ Run task on schedule?
│  └─→ USE: Celery Beat ✅
│      Example: Expire bookings every 60s
│
└─ Handle user request?
   └─→ USE: Django ✅
       Example: All HTTP requests
```

---

## 🚨 Error Handling Flow

```
SCENARIO: User Refreshes Payment Page

1. Frontend JS detects refresh
   ↓
2. sessionStorage check
   ├─→ New tab? → Show error page ✅
   └─→ Refresh? → Continue below
   ↓
3. Call /api/cancel_booking/
   ↓
4. Backend: force_expire_booking()
   ├─→ Update DB: status = EXPIRED
   ├─→ Clear Redis: seat_lock:*
   ├─→ Clear Redis: seat_reservation_*
   └─→ Clear Redis: reserved_seats_*
   ↓
5. Frontend: Show error page
   └─→ "Booking expired. Start new booking?"
```

---

## 📊 System Health Dashboard

```
┌─────────────────────────────────────────────┐
│           COMPONENT STATUS                  │
├─────────────────────────────────────────────┤
│ ✅ Django           Running on :8000        │
│ ✅ Redis            Running on :6379        │
│ ✅ Celery Worker    3 tasks completed       │
│ ✅ Celery Beat      Running every 60s       │
│ ✅ Database         28 bookings today       │
│ ✅ Razorpay         Test mode active        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│         REDIS KEY STATISTICS                │
├─────────────────────────────────────────────┤
│ Seat Locks:              12 keys            │
│ User Reservations:       4 keys             │
│ Reserved Seats Lists:    3 keys             │
│ Total Memory Used:       2.1 MB             │
│ Keys Expiring Soon:      5 (< 5 min)        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│         CELERY TASK STATISTICS              │
├─────────────────────────────────────────────┤
│ Tasks Today:             47                 │
│ ├─ Email Sent:           38 ✅               │
│ ├─ Expired Bookings:     7 ✅                │
│ └─ Failed:               2 ❌                │
│ Average Task Time:       2.3s               │
│ Queue Length:            0 (empty)          │
└─────────────────────────────────────────────┘
```

---

## 🎯 Performance Metrics

```
OPERATION                  | TIME      | COMPONENT
---------------------------|-----------|------------------
Check seat availability    | ~1 ms     | Redis (cache hit)
Lock seats                 | ~5 ms     | Redis
Create booking             | ~50 ms    | Database
Create Razorpay order      | ~200 ms   | Razorpay API
Process payment            | ~2 sec    | Razorpay
Verify signature           | ~10 ms    | Django (HMAC)
Confirm booking            | ~100 ms   | Database + Redis
Queue email task           | ~5 ms     | Redis (Celery)
Send email (async)         | ~2 sec    | Celery (background)

TOTAL USER WAIT TIME: ~2.5 seconds (without email)
USER SEES: "Booking confirmed!" immediately
BACKGROUND: Email sends 5 seconds later
```

---

## 🔐 Security Layers

```
Layer 1: HTTPS
         └─→ All data encrypted in transit

Layer 2: CSRF Protection
         └─→ Prevent cross-site attacks

Layer 3: Session Management
         └─→ Secure user sessions in Redis

Layer 4: Payment Security
         ├─→ No card data stored
         ├─→ Razorpay handles PCI compliance
         └─→ Signature verification (HMAC-SHA256)

Layer 5: Rate Limiting (Planned)
         └─→ Prevent brute force attacks

Layer 6: Input Validation
         └─→ Sanitize all user input
```

---

## 📱 Responsive Design

```
┌─────────────────────────────────┐
│         DESKTOP (1920px)        │
├─────────────────────────────────┤
│ [Header]                        │
│                                 │
│ [Movie Details]  [Seat Layout]  │
│                                 │
│ [Theater Info]   [Price Info]   │
│                                 │
│        [Book Now Button]        │
└─────────────────────────────────┘

┌──────────────┐
│ MOBILE (375px)│
├──────────────┤
│  [Header]    │
│              │
│ [Movie Info] │
│              │
│ [Seat Layout]│
│  (scrollable)│
│              │
│ [Price Info] │
│              │
│ [Book Button]│
└──────────────┘
```

---

## 🎓 Learning Roadmap

```
Week 1: Basics
├─ Day 1-2: Django fundamentals
├─ Day 3-4: Redis basics
└─ Day 5-7: Celery introduction

Week 2: Integration
├─ Day 1-2: Redis + Django
├─ Day 3-4: Celery + Django
└─ Day 5-7: Razorpay integration

Week 3: Advanced
├─ Day 1-2: Concurrency & locking
├─ Day 3-4: Error handling
└─ Day 5-7: Testing & debugging

Week 4: Production
├─ Day 1-2: Deployment setup
├─ Day 3-4: Monitoring & logging
└─ Day 5-7: Performance optimization
```

---

## 🚀 Next Steps

1. **Read**: Start with [UNDERSTANDING_REDIS.md](./UNDERSTANDING_REDIS.md)
2. **Practice**: Run test scripts and watch the logs
3. **Experiment**: Try different scenarios (refresh, cancel, etc.)
4. **Build**: Create your own features on top of this system

---

**Remember**: This visual guide is a quick reference. For detailed explanations, see the full documentation! 📚

*Last Updated: January 3, 2026*
