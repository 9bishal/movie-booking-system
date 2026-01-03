# 📚 Movie Booking System - Complete Documentation Index

Welcome! This is your guide to understanding how the movie booking system works.

---

## 🎯 For Beginners - Start Here!

If you're new to the system, read these guides in order:

### 1. 🗄️ **Understanding Redis** ⭐ START HERE
**File:** [UNDERSTANDING_REDIS.md](./UNDERSTANDING_REDIS.md)

**What you'll learn:**
- What is Redis and why we need it
- How seat locking works
- Redis data structures (keys, values, TTL)
- Real examples with timeline

**Why read first:** Redis is the foundation of our seat reservation system. Understanding it makes everything else easier!

**Time to read:** 20 minutes

---

### 2. ⚙️ **Understanding Celery**
**File:** [UNDERSTANDING_CELERY.md](./UNDERSTANDING_CELERY.md)

**What you'll learn:**
- What is Celery and why we need background tasks
- How email sending works asynchronously
- Celery Beat (scheduled tasks)
- How expired bookings are cleaned up

**Why read second:** Celery handles all the "slow stuff" so users don't have to wait. It's crucial for good user experience!

**Time to read:** 25 minutes

---

### 3. 💳 **Understanding Razorpay**
**File:** [UNDERSTANDING_RAZORPAY.md](./UNDERSTANDING_RAZORPAY.md)

**What you'll learn:**
- What is a payment gateway
- How Razorpay integration works
- Payment security and signature verification
- Test vs live mode

**Why read third:** Payments are the heart of any booking system. Razorpay makes it secure and easy!

**Time to read:** 25 minutes

---

### 4. 🎬 **How Everything Works Together** ⭐ MUST READ
**File:** [HOW_EVERYTHING_WORKS_TOGETHER.md](./HOW_EVERYTHING_WORKS_TOGETHER.md)

**What you'll learn:**
- Complete booking flow (step-by-step)
- How Redis, Celery, and Razorpay interact
- Timeline of a real booking
- What happens when things go wrong

**Why read last:** This ties everything together with real-world examples and shows the complete picture!

**Time to read:** 30 minutes

---

## 🛠️ Technical Documentation

### System Architecture & Fixes

#### **Complete Fix Summary**
**File:** [COMPLETE_FIX_SUMMARY.md](./COMPLETE_FIX_SUMMARY.md)

Complete summary of all seat locking, refresh, and expiry fixes. Includes:
- Client-side expiry (refresh detection, modal dismiss, timer)
- Backend expiry (Celery cleanup)
- Redis key management
- Test results

---

#### **Celery Expiry Redis Fix**
**File:** [CELERY_EXPIRY_REDIS_FIX_COMPLETE.md](./CELERY_EXPIRY_REDIS_FIX_COMPLETE.md)

Detailed explanation of the fix for Celery task not cleaning up user reservation keys in Redis.

---

#### **Refresh and Cancel Fix**
**File:** [REFRESH_AND_CANCEL_FIX.md](./REFRESH_AND_CANCEL_FIX.md)

How the system handles page refreshes, Razorpay modal dismissals, and timer expiry.

---

#### **Redis Fix Complete**
**File:** [REDIS_FIX_COMPLETE.md](./REDIS_FIX_COMPLETE.md)

Fix for user reservation keys not being deleted from Redis when seats are released.

---

#### **New Tab Fix Documentation**
**File:** [NEW_TAB_FIX_DOCUMENTATION.md](./NEW_TAB_FIX_DOCUMENTATION.md)

How the system distinguishes between refresh and opening in a new tab.

---

## 🧪 Testing Documentation

### Test Scripts

All test scripts are in the root directory with prefix `test_`:

1. **test_celery_expiry_redis_cleanup.py** - Verifies Celery expiry cleans up all Redis keys
2. **test_redis_seat_release.py** - Tests Redis key cleanup on force expiry
3. **test_timer_expiry.py** - Tests client-side timer expiry
4. **test_cancel_booking.py** - Tests cancel API endpoint
5. **test_improved_refresh.py** - Tests refresh detection
6. **test_summary_refresh.py** - Tests summary page refresh
7. **test_razorpay_cancel.py** - Tests Razorpay modal dismiss
8. **test_refresh_detection.py** - Tests refresh vs new tab

**How to run:**
```bash
python test_celery_expiry_redis_cleanup.py
```

---

## 📖 Additional Guides

### **Services Guide**
**File:** [services_guide.md](./services_guide.md)

Explanation of the service layer architecture (BookingService, PaymentVerificationService, etc.)

---

### **Caching Guide**
**File:** [bookings/caching_guide.md](./bookings/caching_guide.md)

Detailed guide on how caching works in the bookings app.

---

### **JavaScript API Interaction**
**File:** [js_api_interaction.md](./js_api_interaction.md)

How frontend JavaScript interacts with backend APIs.

---

## 🎓 Learning Path

### For Complete Beginners

```
Day 1: Read UNDERSTANDING_REDIS.md
       → Practice: Use redis-cli to see keys during booking

Day 2: Read UNDERSTANDING_CELERY.md
       → Practice: Watch Celery logs during booking

Day 3: Read UNDERSTANDING_RAZORPAY.md
       → Practice: Create test payment with test card

Day 4: Read HOW_EVERYTHING_WORKS_TOGETHER.md
       → Practice: Follow a complete booking in system logs

Day 5: Read COMPLETE_FIX_SUMMARY.md
       → Practice: Test refresh scenarios
```

### For Intermediate Developers

```
1. Read HOW_EVERYTHING_WORKS_TOGETHER.md (overview)
2. Read COMPLETE_FIX_SUMMARY.md (implementation details)
3. Read component-specific guides as needed
4. Run test scripts to verify understanding
```

### For Advanced Developers

```
1. Read COMPLETE_FIX_SUMMARY.md
2. Review source code in bookings/
3. Read specific fix documentation as needed
4. Modify and extend the system
```

---

## 🔍 Quick Reference

### Find Information By Topic

| Topic | File | Section |
|-------|------|---------|
| Seat locking | UNDERSTANDING_REDIS.md | How Redis Works |
| Booking expiry | UNDERSTANDING_CELERY.md | Celery Beat |
| Payment flow | UNDERSTANDING_RAZORPAY.md | Payment Flow |
| Refresh handling | COMPLETE_FIX_SUMMARY.md | Client-Side Expiry |
| Redis cleanup | CELERY_EXPIRY_REDIS_FIX_COMPLETE.md | Fix Applied |
| Timer expiry | REFRESH_AND_CANCEL_FIX.md | Timer Expiry |
| Signature verification | UNDERSTANDING_RAZORPAY.md | Security & Verification |
| Background tasks | UNDERSTANDING_CELERY.md | Common Tasks |

---

## 🚀 Quick Start Guide

### 1. Setup Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
redis-server

# Start Django
python manage.py runserver

# Start Celery Worker (new terminal)
celery -A moviebooking worker --loglevel=info

# Start Celery Beat (new terminal)
celery -A moviebooking beat --loglevel=info
```

### 2. Test the System
```bash
# Run comprehensive test
python test_celery_expiry_redis_cleanup.py

# Expected output:
# 🎉 ALL CHECKS PASSED!
# ✅ Celery expiry task correctly cleans up all Redis keys
```

### 3. Monitor During Booking
```bash
# Terminal 1: Watch Redis keys
redis-cli MONITOR

# Terminal 2: Watch Celery logs
tail -f celery_worker.log

# Terminal 3: Watch Django logs
tail -f logs/booking.log

# Now make a booking and watch all three!
```

---

## 📞 Need Help?

### Common Issues & Solutions

| Issue | Solution Document | Section |
|-------|------------------|---------|
| Seats still reserved after expiry | CELERY_EXPIRY_REDIS_FIX_COMPLETE.md | Troubleshooting |
| Refresh not detected | NEW_TAB_FIX_DOCUMENTATION.md | Implementation |
| Payment not confirming | UNDERSTANDING_RAZORPAY.md | Troubleshooting |
| Email not sending | UNDERSTANDING_CELERY.md | Troubleshooting |
| Redis keys piling up | UNDERSTANDING_REDIS.md | Troubleshooting |

---

## 📊 System Status Checklist

Use this to verify everything is working:

- [ ] Redis is running (`redis-cli ping` returns PONG)
- [ ] Django server is running (`http://localhost:8000`)
- [ ] Celery worker is running (check process list)
- [ ] Celery beat is running (check process list)
- [ ] Can create booking (seats get locked in Redis)
- [ ] Can complete payment (booking confirmed in database)
- [ ] Email is sent (check Celery logs)
- [ ] Expired bookings are cleaned up (check Celery beat logs)
- [ ] Redis keys are cleaned up (run test scripts)

---

## 🎯 Learning Objectives

After reading all documentation, you should be able to:

✅ Explain what Redis is and why we use it  
✅ Describe how seat locking works with TTL  
✅ Explain what Celery does and why it's needed  
✅ Describe how Celery Beat schedules tasks  
✅ Explain how Razorpay payment flow works  
✅ Describe signature verification and why it's critical  
✅ Trace a complete booking from start to finish  
✅ Explain what happens when user refreshes payment page  
✅ Describe how expired bookings are cleaned up  
✅ Debug issues using Redis CLI and Celery logs  

---

## 🌟 Best Practices

### When Working With This System

1. **Always Check Redis First**: Before debugging seat issues, check Redis keys
2. **Monitor Celery Logs**: Background tasks can fail silently, always check logs
3. **Verify Signatures**: Never skip payment signature verification
4. **Test Edge Cases**: Always test refresh, modal dismiss, timer expiry
5. **Use Test Mode**: Use Razorpay test keys during development
6. **Clean Up Redis**: If testing, manually clean Redis between tests

---

## 📝 Contributing

If you make changes to the system:

1. Update relevant documentation
2. Add test scripts for new features
3. Document any new Redis keys used
4. Update this index if adding new docs

---

## 🎉 You're Ready!

Start with [UNDERSTANDING_REDIS.md](./UNDERSTANDING_REDIS.md) and work your way through the guides. Take your time, try the examples, and refer back to this index whenever you need to find something specific.

**Happy Learning! 🚀**

---

*Last Updated: January 3, 2026*  
*System Version: 2.0.0 (Production Ready)*
