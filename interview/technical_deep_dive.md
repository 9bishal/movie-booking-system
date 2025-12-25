# Technical Deep-Dive: Concurrency, Payments & Scalability

This document explains the "Why, How, and When" behind the core architectural decisions made in the movie booking system. It is designed to prepare you for technical interviews by explaining complex concepts like race conditions, distributed locking, and event-driven architecture.

---

## 🏎️ The "Race Condition" Problem

**Q: What is a Race Condition in the context of movie booking?**
**A:** Imagine two users, Alice and Bob, both looking at Seat A1 at the same time.

1. Alice checks availability → System says "A1 is free".
2. Bob checks availability → System says "A1 is free".
3. Alice pays for A1.
4. Bob pays for A1.
   **Result:** Double Booking. This happens because the "Check" and "Action" are not connected in one atomic step.

---

## 🛡️ The "Triple-Shield" Protection

**Q: How does your system ensure "Race-Condition Proof" bookings?**
**A:** We use a three-layered defense strategy:

### 1. Redis Optimistic Lock (The Traffic Controller)

- **Why:** Database queries are slow. Redis is extremely fast (RAM-based).
- **How:** When a user selects seats, we create a `seat_reservation_{showtime}_{user}` key in Redis with a 10-minute TTL (Time To Live).
- **When:** Triggers during seat selection and again _during_ the booking creation phase.

### 2. UI Live Synchronization (The User Guard)

- **Why:** Users should never be surprised by a timeout.
- **How:** We pass the exact Redis TTL to the frontend. A JavaScript timer redirects the user the moment the lock expires.
- **When:** Active on the Booking Summary and Payment pages.

### 3. Backend Authority Model (The Final Judge)

- **Why:** Razorpay modal might stay open longer than our Redis lock (Client-side control is never 100% reliable).
- **How:** In the `payment_success` view, we perform a **Final Verification**. We re-check the database for any new `CONFIRMED` bookings for those specific seats before issuing a ticket.
- **When:** Triggers _after_ the money is captured but _before_ the ticket is generated.

---

## 🚀 Redis vs. Database

**Q: Why use Redis for seat locking instead of just the SQL database?**
**A:**

- **Latency:** Redis responds in microseconds, ensuring the UI feels "snappy" during high-traffic sales.
- **Auto-Expiry:** Redis handles the cleanup for us. If a user abandons their cart, Redis automatically "releases" the seats when the TTL expires.
- **Concurrency:** Redis is single-threaded at its core, making it naturally gifted at handling atomic operations (like checking if a key exists and setting it in one go).

---

## ⚙️ Celery & Background Tasks

**Q: Why do we use Celery for sending confirmation emails?**
**A:**

- **User Experience:** Sending an email takes 2-3 seconds. If we did this "in-process," the user would be stuck on a loading screen after paying.
- **Resilience:** If the email server is down, Celery can automatically retry the task later without affecting the main application.
- **Scalability:** We can have 100 users booking tickets simultaneously, and a separate "Worker" can handle the email queue in the background.

---

## 💳 Razorpay Integration

**Q: Why do we anchor the `razorpay_order_id` to the booking in our DB?**
**A:** This prevents "Payment Hijacking." If we didn't save the order ID, a malicious user could potentially capture a successful payment response from _another_ transaction and try to apply it to a new booking. By anchoring the ID, we ensure the payment we receive is exactly for the booking we created.

---

🎬 **Knowledge Check:**

> "The goal of a robust system isn't just to make things work; it's to handle what happens when things fail, timeout, or collide."
