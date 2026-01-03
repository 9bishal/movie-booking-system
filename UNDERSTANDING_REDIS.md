# 🏗️ Understanding Redis in Movie Booking System
## A Beginner's Guide

---

## 📚 Table of Contents
1. [What is Redis?](#what-is-redis)
2. [Why We Use Redis](#why-we-use-redis)
3. [How Redis Works in Our System](#how-redis-works-in-our-system)
4. [Redis Data Structures We Use](#redis-data-structures-we-use)
5. [Real-World Example](#real-world-example)
6. [Common Commands](#common-commands)
7. [Troubleshooting](#troubleshooting)

---

## 🤔 What is Redis?

**Redis** stands for **RE**mote **DI**ctionary **S**erver. Think of it as a **super-fast digital notepad** that lives in your computer's memory (RAM).

### Simple Analogy 🎯
Imagine you're at a movie theater ticket counter:
- **Database (SQLite/PostgreSQL)** = Filing cabinet with permanent records (slow but permanent)
- **Redis** = Sticky notes on the counter (fast but temporary)

When you reserve a seat:
- You quickly put a sticky note (Redis) saying "John reserved A1"
- If payment succeeds, you file it permanently (Database)
- If payment fails, you throw away the sticky note (Redis auto-expires)

### Key Characteristics
- **Fast**: Stores data in RAM (memory), not disk → 1000x faster than database
- **Temporary**: Data can expire automatically (perfect for "hold this seat for 10 minutes")
- **Simple**: Just key-value pairs like a dictionary in Python
- **In-Memory**: All data in RAM → super fast but lost if server restarts (unless configured otherwise)

---

## 🎯 Why We Use Redis

### Problem Without Redis ❌
```python
# Using only database for seat reservation
def reserve_seat():
    # Check database if seat is free
    seat = Seat.objects.get(id='A1')
    if seat.is_booked:
        return "Sorry, taken!"
    
    # Mark as reserved in database
    seat.is_reserved = True
    seat.save()  # Slow disk write!
    
    # Problem: What if user never completes payment?
    # Seat stays "reserved" forever! 😱
```

### Solution With Redis ✅
```python
# Using Redis for temporary reservation
def reserve_seat():
    # Check Redis cache (super fast!)
    if redis.get('seat_A1'):
        return "Sorry, taken!"
    
    # Reserve in Redis with 10-minute expiry
    redis.setex('seat_A1', 600, user_id)
    # After 10 minutes, Redis automatically deletes it!
    
    # If payment succeeds, then save to database
    # If payment fails, Redis auto-cleans up
```

### Why This is Better
1. **Speed**: Redis operations take ~1ms vs database ~50ms
2. **Auto-Cleanup**: Expired reservations disappear automatically
3. **Less Database Load**: Thousands of reservations don't clutter the database
4. **Better UX**: Users see real-time seat availability

---

## 🎬 How Redis Works in Our System

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                        USER                                  │
│                 (Selecting Seats)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    DJANGO SERVER                             │
│  1. User selects seats A1, A2                                │
│  2. Server checks Redis: Are these seats free?               │
│  3. If free, reserve in Redis for 10 minutes                │
│  4. Create PENDING booking in database                       │
└────────────────────────┬────────────────────────────────────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
    ┌───────────────┐         ┌───────────────┐
    │     REDIS     │         │   DATABASE    │
    │   (CACHE)     │         │  (PERMANENT)  │
    ├───────────────┤         ├───────────────┤
    │ Temporary:    │         │ Permanent:    │
    │ • Seat locks  │         │ • Movies      │
    │ • Reservations│         │ • Theaters    │
    │ • User carts  │         │ • Bookings    │
    │               │         │ • Users       │
    │ Auto-expires  │         │ Never expires │
    │ after 10 min  │         │ (unless deleted)│
    └───────────────┘         └───────────────┘
```

### Flow: From Seat Selection to Payment

```
Step 1: User Clicks "Select Seats A1, A2"
┌────────────────────────────────────────┐
│ Django: Call reserve_seats()           │
│ Redis: Check if A1, A2 are free       │
│ Redis: SETNX seat_lock:24:A1 = user_7 │
│ Redis: SETNX seat_lock:24:A2 = user_7 │
│ Redis: EXPIRE 600 seconds (10 min)    │
└────────────────────────────────────────┘
           Status: ✅ Seats Reserved

Step 2: User Proceeds to Payment
┌────────────────────────────────────────┐
│ Django: Create Booking (status=PENDING)│
│ Database: Save booking record          │
│ Redis: Still holding seat locks        │
└────────────────────────────────────────┘
           Status: 🕐 Waiting for Payment

Step 3a: User Completes Payment ✅
┌────────────────────────────────────────┐
│ Django: Payment successful!            │
│ Database: Update booking (CONFIRMED)   │
│ Redis: DELETE seat locks (released)    │
│ Redis: Add to reserved_seats list      │
└────────────────────────────────────────┘
           Status: ✅ Booking Confirmed!

Step 3b: User Abandons Payment ❌
┌────────────────────────────────────────┐
│ Time Passes: 10 minutes elapse...     │
│ Redis: Auto-deletes seat locks (TTL)   │
│ Celery Task: Finds expired booking     │
│ Django: Update booking (status=EXPIRED)│
│ Redis: Seats now free for others       │
└────────────────────────────────────────┘
           Status: 🔓 Seats Released
```

---

## 🗄️ Redis Data Structures We Use

### 1. **Seat Locks** (Individual Lock per Seat)
```python
# Key Pattern: seat_lock:{showtime_id}:{seat_id}
# Example: seat_lock:24:A1

# What it stores:
{
    "key": "seat_lock:24:A1",
    "value": "7",  # user_id who locked it
    "ttl": 600     # expires in 10 minutes
}

# Purpose: Prevent multiple users from booking same seat
# Expires: 10 minutes (auto-cleanup)
```

**In Code:**
```python
# Reserve seat A1 for showtime 24 by user 7
lock_key = f"seat_lock:{showtime_id}:{seat_id}"
redis.setex(lock_key, 600, user_id)

# Check if seat is locked
is_locked = redis.get(lock_key)
if is_locked:
    print(f"Seat locked by user {is_locked}")
```

### 2. **Reserved Seats List** (All Reserved Seats for a Showtime)
```python
# Key Pattern: reserved_seats_{showtime_id}
# Example: reserved_seats_24

# What it stores:
{
    "key": "reserved_seats_24",
    "value": ["A1", "A2", "B3", "C5"],  # List of seat IDs
    "ttl": 600  # 10 minutes
}

# Purpose: Quick lookup of all reserved seats
# Expires: 10 minutes
```

**In Code:**
```python
# Add seats to reserved list
cache_key = f"reserved_seats_{showtime_id}"
reserved = cache.get(cache_key) or []
reserved.extend(['A1', 'A2'])
cache.set(cache_key, reserved, timeout=600)

# Check if seat is reserved
if 'A1' in reserved:
    print("Seat A1 is reserved!")
```

### 3. **User Reservation** (What User is Currently Booking)
```python
# Key Pattern: seat_reservation_{showtime_id}_{user_id}
# Example: seat_reservation_24_7

# What it stores:
{
    "key": "seat_reservation_24_7",
    "value": {
        "seat_ids": ["A1", "A2"],
        "reserved_at": 1767451157.506  # timestamp
    },
    "ttl": 600  # 10 minutes
}

# Purpose: Track what specific user is booking
# Critical: Must be deleted when booking expires/cancels!
```

**In Code:**
```python
# Save user's reservation
reservation_key = f"seat_reservation_{showtime_id}_{user_id}"
reservation_data = {
    'seat_ids': ['A1', 'A2'],
    'reserved_at': time.time()
}
cache.set(reservation_key, reservation_data, timeout=600)

# Get user's reservation
user_reservation = cache.get(reservation_key)
if user_reservation:
    seats = user_reservation['seat_ids']
    print(f"User reserved: {seats}")
```

### 4. **Available Seats** (All Free Seats for a Showtime)
```python
# Key Pattern: available_seats_{showtime_id}
# Example: available_seats_24

# What it stores:
{
    "key": "available_seats_24",
    "value": ["A1", "A2", "A3", ..., "Z10"],  # All free seats
    "ttl": 3600  # 1 hour (longer than reservations)
}

# Purpose: Fast lookup of free seats
# Expires: 1 hour
```

---

## 🎭 Real-World Example

Let's follow a complete booking flow:

### Scenario: John wants to book seats A1 and A2 for "Avengers" at 7 PM

#### **Time: 6:00 PM** - John Selects Seats
```python
# 1. Django receives request
def select_seats(request, showtime_id, seat_ids=['A1', 'A2']):
    user_id = request.user.id  # John's ID = 7
    
    # 2. Check Redis if seats are available
    reserved_seats = cache.get(f"reserved_seats_{showtime_id}") or []
    
    # 3. Are A1, A2 already reserved?
    if 'A1' in reserved_seats or 'A2' in reserved_seats:
        return "Sorry, seats taken!"
    
    # 4. Reserve in Redis (all 3 keys!)
    
    # Key 1: Individual locks
    cache.setex(f"seat_lock:{showtime_id}:A1", 600, user_id)
    cache.setex(f"seat_lock:{showtime_id}:A2", 600, user_id)
    
    # Key 2: Add to reserved list
    reserved_seats.extend(['A1', 'A2'])
    cache.set(f"reserved_seats_{showtime_id}", reserved_seats, 600)
    
    # Key 3: Save user's reservation
    cache.set(f"seat_reservation_{showtime_id}_{user_id}", {
        'seat_ids': ['A1', 'A2'],
        'reserved_at': time.time()
    }, 600)
    
    return "Seats reserved! Complete payment in 10 minutes"
```

**Redis State:**
```
✅ seat_lock:24:A1 = "7" (expires 6:10 PM)
✅ seat_lock:24:A2 = "7" (expires 6:10 PM)
✅ reserved_seats_24 = ["A1", "A2"]
✅ seat_reservation_24_7 = {"seat_ids": ["A1", "A2"], ...}
```

#### **Time: 6:02 PM** - John Opens Payment Page
```python
# John sees Razorpay modal, but doesn't complete payment yet
# Redis still holding seats (8 minutes remaining)
```

**Redis State:** (No change, TTL counting down)
```
✅ seat_lock:24:A1 = "7" (expires in 8 min)
✅ seat_lock:24:A2 = "7" (expires in 8 min)
✅ reserved_seats_24 = ["A1", "A2"] (expires in 8 min)
✅ seat_reservation_24_7 = {...} (expires in 8 min)
```

#### **Time: 6:05 PM** - Jane Tries to Book A1
```python
# Jane (user_id=8) tries to book same seat A1
def select_seats(request, showtime_id, seat_ids=['A1']):
    reserved_seats = cache.get(f"reserved_seats_{showtime_id}")
    # reserved_seats = ["A1", "A2"]
    
    if 'A1' in reserved_seats:
        return "Sorry, A1 is reserved by someone else!"
        # Jane gets error, can't book A1 ❌
```

#### **Time: 6:08 PM** - John Completes Payment ✅
```python
# John pays successfully via Razorpay
def confirm_payment(booking_id, payment_id):
    booking = Booking.objects.get(id=booking_id)
    booking.status = 'CONFIRMED'
    booking.payment_id = payment_id
    booking.save()  # Permanent database record
    
    # Release Redis locks (no longer needed)
    cache.delete(f"seat_lock:{showtime_id}:A1")
    cache.delete(f"seat_lock:{showtime_id}:A2")
    cache.delete(f"seat_reservation_{showtime_id}_{user_id}")
    
    # Keep in reserved list (permanently booked)
    # or move to confirmed_bookings in database
```

**Redis State:**
```
❌ seat_lock:24:A1 = DELETED
❌ seat_lock:24:A2 = DELETED
❌ seat_reservation_24_7 = DELETED
✅ Database: Booking CONFIRMED ✅
```

#### **Alternative: 6:11 PM** - John Abandons Payment ❌
```python
# John closed the browser, never completed payment
# Redis TTL expires automatically after 10 minutes

# At 6:10 PM, Redis auto-deletes:
# ❌ seat_lock:24:A1 (TTL=0, deleted)
# ❌ seat_lock:24:A2 (TTL=0, deleted)
# ❌ reserved_seats_24 (TTL=0, deleted)
# ❌ seat_reservation_24_7 (TTL=0, deleted)

# At 6:11 PM, Celery task runs:
@task
def release_expired_bookings():
    expired = Booking.objects.filter(
        status='PENDING',
        expires_at__lt=timezone.now()
    )
    for booking in expired:
        booking.status = 'EXPIRED'
        booking.save()
        # Seats now free for others! ✅
```

**Final State:**
```
Redis: All keys deleted (auto-expired)
Database: Booking marked as EXPIRED
Result: A1 and A2 now available for Jane to book! 🎉
```

---

## 🛠️ Common Redis Commands

### From Python (Django)
```python
from django.core.cache import cache

# Set a value (expires in 10 minutes)
cache.set('my_key', 'my_value', timeout=600)

# Set with expiry (same as above)
cache.setex('my_key', 600, 'my_value')

# Get a value
value = cache.get('my_key')  # Returns 'my_value' or None

# Delete a value
cache.delete('my_key')

# Check if exists
exists = cache.get('my_key') is not None

# Get with default
value = cache.get('my_key', default='not_found')
```

### From Redis CLI (Terminal)
```bash
# Connect to Redis
redis-cli

# Set a value
SET mykey "Hello"

# Get a value
GET mykey

# Set with expiry (600 seconds = 10 minutes)
SETEX seat_lock:24:A1 600 "7"

# Check time to live (TTL)
TTL seat_lock:24:A1
# Returns: 550 (seconds remaining)

# List all keys matching pattern
KEYS seat_lock:*
# Returns: seat_lock:24:A1, seat_lock:24:A2, ...

# Delete a key
DEL seat_lock:24:A1

# Delete all keys (DANGEROUS!)
FLUSHALL

# Check if Redis is running
PING
# Returns: PONG
```

---

## 🔧 Troubleshooting

### Problem 1: "Seat already reserved" but I just released it!
```bash
# Check if Redis key still exists
redis-cli
> GET seat_reservation_24_7
> TTL seat_reservation_24_7

# If it exists, manually delete
> DEL seat_reservation_24_7
> DEL seat_lock:24:A1
> DEL seat_lock:24:A2
```

### Problem 2: Redis not responding
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running, start it
redis-server
# Or on macOS with Homebrew:
brew services start redis
```

### Problem 3: Can't connect to Redis from Django
```python
# Check settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',  # Correct URL?
    }
}

# Test connection
from django.core.cache import cache
cache.set('test', 'hello')
print(cache.get('test'))  # Should print: hello
```

### Problem 4: Too many keys in Redis (memory full)
```bash
# Count all keys
redis-cli DBSIZE

# See memory usage
redis-cli INFO memory

# Delete old/expired keys
redis-cli
> KEYS seat_lock:*  # List all seat locks
> DEL seat_lock:old_showtime:A1  # Delete individually
# Or wait for TTL to auto-delete
```

---

## 📊 Redis vs Database Comparison

| Feature | Redis | Database (SQLite/PostgreSQL) |
|---------|-------|------------------------------|
| **Speed** | 🚀 ~1ms | 🐌 ~50ms |
| **Storage** | RAM (memory) | Disk (hard drive) |
| **Persistence** | Temporary (expires) | Permanent |
| **Best For** | Caching, sessions, locks | User data, bookings, movies |
| **Data Loss** | Lost on restart | Never lost |
| **Cost** | Cheap (RAM) | Cheaper (disk) |
| **Size Limit** | GB (RAM size) | TB (disk size) |

---

## 🎓 Key Takeaways

1. **Redis = Fast Temporary Storage**: Perfect for seat reservations that expire
2. **Auto-Expiry = Auto-Cleanup**: No manual cleanup needed, Redis does it
3. **Three Keys per Reservation**: seat_lock, reserved_seats, seat_reservation
4. **TTL = Time To Live**: Countdown timer for automatic deletion
5. **Database = Permanent**: Only confirmed bookings go here
6. **Speed Matters**: Redis makes real-time seat availability possible

---

## 🚀 Next Steps

1. Read: [Understanding Celery](./UNDERSTANDING_CELERY.md) - Learn about background tasks
2. Read: [Understanding Razorpay](./UNDERSTANDING_RAZORPAY.md) - Learn about payments
3. Practice: Use `redis-cli` to inspect keys during a booking
4. Experiment: Try changing TTL values and see the effect

---

**Remember**: Redis is like a smart sticky note system - fast, temporary, and self-cleaning! 📝⚡

*Last Updated: January 3, 2026*
