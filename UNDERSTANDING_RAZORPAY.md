# 💳 Understanding Razorpay in Movie Booking System
## A Beginner's Guide

---

## 📚 Table of Contents
1. [What is Razorpay?](#what-is-razorpay)
2. [Why We Need Razorpay](#why-we-need-razorpay)
3. [How Razorpay Works](#how-razorpay-works)
4. [Payment Flow in Our System](#payment-flow-in-our-system)
5. [Razorpay Integration](#razorpay-integration)
6. [Real-World Example](#real-world-example)
7. [Security & Verification](#security--verification)
8. [Troubleshooting](#troubleshooting)

---

## 🤔 What is Razorpay?

**Razorpay** is a **payment gateway** - a service that lets you accept online payments (credit cards, debit cards, UPI, wallets) without handling sensitive financial data yourself.

### Simple Analogy 🎯
Imagine you're running a movie theater:

**Without Razorpay:**
```
Customer: "Here's my credit card"
You: "Let me process it..."
     - Store card number? 😱 (Illegal without PCI compliance!)
     - Build payment infrastructure? 💸 (Costs millions!)
     - Handle refunds manually? 😫 (Time-consuming!)
     - Support all payment methods? 🤯 (Impossible!)
```

**With Razorpay:**
```
Customer: "I want to pay"
You: "Sure! Please pay through Razorpay"
     [Razorpay modal opens]
Customer: Enters card details (Razorpay handles it securely)
     [Payment processed]
Razorpay: "Payment successful! Here's payment_id: pay_xyz123"
You: "Great! Booking confirmed!" ✅

     - No card data stored on your server ✅
     - All payment methods supported ✅
     - Refunds handled automatically ✅
     - Secure and PCI compliant ✅
```

### Key Characteristics
- **Payment Gateway**: Handles money transactions securely
- **No Card Data**: You never see or store sensitive card information
- **Multiple Methods**: Supports cards, UPI, wallets, net banking
- **Test Mode**: Practice with fake payments before going live
- **Webhooks**: Get notified when payments succeed/fail

---

## 🎯 Why We Need Razorpay

### Problems Without Payment Gateway ❌

#### Problem 1: Security Nightmare
```python
# DON'T EVER DO THIS! ❌❌❌
def process_payment(card_number, cvv, expiry):
    # Storing card details = ILLEGAL without PCI-DSS compliance
    # PCI-DSS compliance costs $50,000+ per year
    # One data breach = lawsuit + bankruptcy
    pass
```

#### Problem 2: Limited Payment Options
```python
# Supporting just credit cards = losing 60% of customers
# In India: UPI, Paytm, PhonePe, Google Pay are more popular
# Each integration = months of work 
```

#### Problem 3: Manual Refunds
```python
# Customer cancels booking
# You have to manually process refund
# Takes 7-10 days, customer unhappy
```

### Solutions With Razorpay ✅

#### Solution 1: Secure & Compliant
```python
# Razorpay handles all security
# You just get a payment_id when payment succeeds
# No card data ever touches your server
payment_id = razorpay.payment.fetch('pay_xyz123')
```

#### Solution 2: All Payment Methods
```python
# One integration = all payment methods
# Cards, UPI, wallets, net banking, EMI
# Razorpay adds new methods automatically
```

#### Solution 3: Instant Refunds
```python
# One API call = instant refund
razorpay.payment.refund('pay_xyz123', amount=500)
# Money credited in 5-7 days (bank processing time)
```

---

## 💡 How Razorpay Works

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        YOUR WEBSITE                          │
│                   (Django Server)                            │
│                                                              │
│  1. User clicks "Pay ₹500"                                   │
│  2. Server creates Razorpay Order                            │
│  3. Server shows Razorpay checkout modal                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAZORPAY CHECKOUT                         │
│                   (Secure Payment Modal)                     │
│                                                              │
│  [Enter Card Details]                                        │
│  Card Number: 4111 1111 1111 1111                            │
│  CVV: 123                                                    │
│  Expiry: 12/25                                               │
│                                                              │
│  [Pay ₹500] ←─── Customer clicks                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAZORPAY BACKEND                          │
│               (Payment Processing)                           │
│                                                              │
│  1. Validate card with bank                                  │
│  2. Process payment                                          │
│  3. If successful, generate payment_id                       │
│  4. Return result to your website                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        YOUR WEBSITE                          │
│                   (Payment Success)                          │
│                                                              │
│  1. Receive payment_id: "pay_xyz123"                         │
│  2. Verify signature (security check)                        │
│  3. Mark booking as CONFIRMED                                │
│  4. Show success page to user                                │
└─────────────────────────────────────────────────────────────┘
```

### Key Concepts

#### 1. **Order** (Created by Your Server)
```python
# Your server creates an order BEFORE showing payment modal
order = {
    'id': 'order_abc123',
    'amount': 50000,  # Amount in paise (₹500.00)
    'currency': 'INR',
    'receipt': 'booking_12345',
    'notes': {
        'booking_id': 12345,
        'user_id': 7
    }
}
```

Think of it as a **bill** - you create it, customer pays it.

#### 2. **Payment** (Created by Razorpay)
```python
# Razorpay creates payment when customer pays
payment = {
    'id': 'pay_xyz789',
    'order_id': 'order_abc123',
    'amount': 50000,
    'status': 'captured',  # Money received!
    'method': 'card',
    'card': {
        'network': 'Visa',
        'last4': '1111'
    }
}
```

Think of it as a **receipt** - proof of payment.

#### 3. **Signature** (Security Verification)
```python
# Razorpay sends signature to prove payment is genuine
signature = 'abc123def456...'

# You verify it using your secret key
# If valid = payment is real
# If invalid = potential fraud, reject it!
```

Think of it as a **seal** on a certificate - proves authenticity.

---

## 🎬 Payment Flow in Our System

### Step-by-Step Process

#### **Step 1: User Selects Seats**
```python
# File: bookings/views.py

def select_seats(request):
    # User picks seats A1, A2
    seats = ['A1', 'A2']
    
    # Reserve in Redis (10-minute lock)
    SeatManager.reserve_seats(showtime_id, seats, user.id)
    
    # Create PENDING booking
    booking = Booking.objects.create(
        user=user,
        showtime=showtime,
        seats=seats,
        total_amount=500.00,
        status='PENDING',
        expires_at=now() + timedelta(minutes=10)
    )
    
    return redirect('booking_summary', booking.id)
```

#### **Step 2: User Confirms Booking**
```python
# File: bookings/views.py

def booking_summary(request, booking_id): 
    booking = Booking.objects.get(id=booking_id)
    
    # Show summary page with "Proceed to Payment" button
    context = {
        'booking': booking,
        'seats': booking.seats,
        'total': booking.total_amount
    }
    
    return render('booking_summary.html', context)
```

#### **Step 3: User Clicks "Proceed to Payment"**
```python
# File: bookings/views.py

def payment_page(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    
    # Create Razorpay order (or reuse existing)
    order_data = BookingService.get_or_create_razorpay_order(booking)
    
    if not order_data['success']:
        return render('error.html', {'message': 'Payment failed'})
    
    # Pass order details to template
    context = {
        'booking': booking,
        'order_id': order_data['order_id'],
        'amount': order_data['amount'],
        'razorpay_key': settings.RAZORPAY_KEY_ID
    }
    
    return render('payment.html', context)
```

#### **Step 4: Frontend Shows Razorpay Modal**
```javascript
// File: bookings/templates/bookings/payment.html

// Razorpay configuration
var options = {
    "key": "{{ razorpay_key }}",  // Your API key
    "amount": {{ amount }},        // Amount in paise
    "currency": "INR",
    "order_id": "{{ order_id }}",  // Order ID from backend
    
    "handler": function (response) {
        // Payment successful! ✅
        console.log("Payment ID:", response.razorpay_payment_id);
        console.log("Order ID:", response.razorpay_order_id);
        console.log("Signature:", response.razorpay_signature);
        
        // Send to backend for verification
        verifyPayment(response);
    },
    
    "modal": { 
        "ondismiss": function() {  
            // User closed modal without paying ❌
            console.log("Payment cancelled");
            cancelBooking();
        }
    }
};

// Show Razorpay checkout modal
var rzp = new Razorpay(options);
rzp.open();
```

#### **Step 5: Backend Verifies Payment**
```python
# File: bookings/views.py

def verify_payment(request):
    payment_id = request.POST.get('razorpay_payment_id')
    order_id = request.POST.get('razorpay_order_id')
    signature = request.POST.get('razorpay_signature')
    
    # CRITICAL: Verify signature (security check)
    is_valid = PaymentVerificationService.verify_payment_signature(
        order_id, payment_id, signature
    )
    
    if not is_valid:
        return JsonResponse({'success': False, 'error': 'Invalid signature'})
    
    # Find booking by order_id
    booking = Booking.objects.get(razorpay_order_id=order_id)
    
    # Confirm payment and booking
    success, error = BookingService.confirm_payment(
        booking, payment_id, signature_verified=True
    )
    
    if success:
        return JsonResponse({'success': True, 'booking_id': booking.id})
    else:
        return JsonResponse({'success': False, 'error': error})
```

#### **Step 6: Confirmation & Cleanup**
```python
# File: bookings/services.py

def confirm_payment(booking, payment_id):
    # Update booking
    booking.status = 'CONFIRMED'
    booking.payment_id = payment_id
    booking.confirmed_at = timezone.now()
    booking.save()
    
    # Permanently mark seats as booked
    SeatManager.confirm_seats(booking.showtime.id, booking.seats)
    
    # Send confirmation email (async via Celery)
    send_booking_confirmation_email.delay(booking.id)
    
    return True, None
```

---

## 🔐 Security & Verification

### Why Signature Verification is Critical

**Without Signature Verification:**
```
Hacker: *Opens browser console*
        *Sends fake payment success to your server*
        
POST /verify_payment/
{
    "payment_id": "pay_FAKE123",
    "order_id": "order_abc123",
    "signature": "fake_signature"
}

Your Server: "Looks good! Booking confirmed!" ❌
Hacker: *Gets free tickets* 😈
```

**With Signature Verification:**
```
Hacker: *Sends fake payment*

Your Server: *Verifies signature using secret key*
              *Signature doesn't match!*
              "Invalid signature, payment rejected!" ✅
              
Hacker: *Can't get free tickets* 😤
```

### How Signature Verification Works

```python
# File: bookings/services.py

def verify_payment_signature(order_id, payment_id, signature):
    """
    Verify that payment came from Razorpay and wasn't tampered with.
    Uses HMAC-SHA256 algorithm with your secret key.
    """
    import hmac
    import hashlib
    
    # Create message by joining order_id and payment_id
    message = f"{order_id}|{payment_id}"
    
    # Calculate expected signature using your secret key
    expected_signature = hmac.new(
        key=settings.RAZORPAY_KEY_SECRET.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    if signature == expected_signature:
        return True  # Valid! ✅
    else:
        return False  # Fraud! ❌
```

**Math Behind It:**
```
Message = "order_abc123|pay_xyz789"
Secret Key = "your_secret_key_123"

Signature = HMAC_SHA256(Message, Secret Key)
         = "a1b2c3d4e5f6..."

Only someone with your secret key can generate valid signatures!
Hackers don't have your secret key = can't fake payments ✅
```

---

## 🎭 Real-World Example

### Scenario: John Books Tickets for ₹500

#### **Step 1: John Clicks "Pay Now"** (6:00 PM)
```python
# Backend creates Razorpay order
order = razorpay_client.order.create({
    'amount': 50000,  # ₹500.00 in paise
    'currency': 'INR',
    'receipt': 'booking_12345',
    'notes': {
        'booking_id': 12345,
        'user_id': 7,
        'user_name': 'John'
    }
})

# Response from Razorpay:
{
    'id': 'order_MfL8Dxyz123',
    'amount': 50000,
    'currency': 'INR',
    'receipt': 'booking_12345',
    'status': 'created'
}

# Save order_id to booking
booking.razorpay_order_id = 'order_MfL8Dxyz123'
booking.save()
```

#### **Step 2: Razorpay Modal Opens**
```javascript
// Frontend shows Razorpay checkout
var rzp = new Razorpay({
    key: "rzp_test_xxxxx",
    amount: 50000,  // ₹500.00
    order_id: "order_MfL8Dxyz123",
    
    handler: function(response) {
        // This runs when payment succeeds
        verifyPayment(response);
    }
});

rzp.open();  // Modal appears to John
```

**John Sees:**
```
┌─────────────────────────────────────┐
│      RAZORPAY CHECKOUT              │
├─────────────────────────────────────┤
│  Pay ₹500.00                        │
│                                     │
│  [Card] [UPI] [Wallet] [NetBanking]│
│                                     │
│  Card Number: ________________      │
│  CVV: ___    Expiry: __/__         │
│                                     │
│  [Pay ₹500] ← John clicks this     │
└─────────────────────────────────────┘
```

#### **Step 3: John Enters Card & Pays** (6:02 PM)
```
John enters: 4111 1111 1111 1111 (Test card)
CVV: 123
Expiry: 12/25

[Razorpay processes payment]
[Bank approves transaction]
[Razorpay generates payment_id]
```

#### **Step 4: Razorpay Returns Success**
```javascript
// Razorpay calls handler function
function handler(response) {
    console.log(response);
    // {
    //   razorpay_payment_id: "pay_MfL8EABCD456",
    //   razorpay_order_id: "order_MfL8Dxyz123",
    //   razorpay_signature: "a1b2c3d4e5f6..."
    // }
    
    // Send to backend for verification
    fetch('/verify_payment/', {
        method: 'POST',
        body: JSON.stringify(response)
    });
}
```

#### **Step 5: Backend Verifies & Confirms**
```python
def verify_payment(request):
    payment_id = "pay_MfL8EABCD456"
    order_id = "order_MfL8Dxyz123"
    signature = "a1b2c3d4e5f6..."
    
    # Verify signature
    is_valid = verify_signature(order_id, payment_id, signature)
    # Returns: True ✅
    
    # Find booking
    booking = Booking.objects.get(razorpay_order_id=order_id)
    
    # Confirm booking
    booking.status = 'CONFIRMED'
    booking.payment_id = payment_id
    booking.save()
    
    # Release Redis locks, confirm seats
    SeatManager.confirm_seats(booking.showtime.id, booking.seats)
    
    # Send email
    send_booking_confirmation_email.delay(booking.id)
    
    return JsonResponse({'success': True})
```

#### **Step 6: John Sees Success Page** (6:03 PM)
```html
<!-- Frontend redirects to success page -->
<div class="success">
    <h1>🎉 Booking Confirmed!</h1>
    <p>Booking Number: BOOK-20260103-12345</p>
    <p>Seats: A1, A2</p>
    <p>Payment ID: pay_MfL8EABCD456</p>
    <p>Check your email for confirmation!</p>
</div>
```

**Timeline:**
```
6:00 PM - Order created
6:02 PM - John enters card details
6:02 PM - Razorpay processes payment
6:02 PM - Payment successful
6:03 PM - Backend verifies signature ✅
6:03 PM - Booking confirmed in database ✅
6:03 PM - Email queued (Celery) ✅
6:03 PM - John sees success page ✅
6:05 PM - John receives email ✅
```

---

## 🛠️ Razorpay Integration Code

### 1. **Creating an Order** (Backend)
```python
# File: bookings/razorpay_utils.py

import razorpay
from django.conf import settings

# Initialize Razorpay client
client = razorpay.Client(auth=(
    settings.RAZORPAY_KEY_ID,
    settings.RAZORPAY_KEY_SECRET
))

def create_order(amount, receipt, notes=None):
    """
    Create a Razorpay order.
    
    Args:
        amount: Amount in rupees (will be converted to paise)
        receipt: Unique receipt ID (e.g., booking number)
        notes: Optional metadata
    
    Returns:
        Order data or error
    """
    try:
        order = client.order.create({
            'amount': int(amount * 100),  # Convert to paise
            'currency': 'INR',
            'receipt': receipt,
            'notes': notes or {}
        })
        
        return {
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency']
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
```

### 2. **Payment Page** (Template)
```html
<!-- File: bookings/templates/bookings/payment.html -->

<!DOCTYPE html>
<html>
<head>
    <!-- Include Razorpay checkout.js -->
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
</head>
<body>
    <h1>Payment</h1>
    <p>Amount: ₹{{ booking.total_amount }}</p>
    
    <button id="pay-button">Pay Now</button>
    
    <script>
        document.getElementById('pay-button').onclick = function() {
            var options = {
                "key": "{{ razorpay_key }}",
                "amount": {{ amount }},  // In paise
                "currency": "INR",
                "order_id": "{{ order_id }}",
                "name": "Movie Booking",
                "description": "Booking #{{ booking.booking_number }}",
                
                "handler": function (response) {
                    // Payment success!
                    verifyPayment(response);
                },
                
                "modal": {
                    "ondismiss": function() {
                        // User closed modal
                        alert("Payment cancelled");
                    }
                },
                
                "theme": {
                    "color": "#F37254"
                }
            };
            
            var rzp = new Razorpay(options);
            rzp.open();
        };
        
        function verifyPayment(response) {
            fetch('/bookings/verify_payment/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                body: JSON.stringify({
                    razorpay_payment_id: response.razorpay_payment_id,
                    razorpay_order_id: response.razorpay_order_id,
                    razorpay_signature: response.razorpay_signature,
                    booking_id: {{ booking.id }}
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/bookings/success/' + data.booking_id + '/';
                } else {
                    alert('Payment verification failed!');
                }
            });
        }
    </script>
</body>
</html>
```

### 3. **Verify Payment** (Backend)
```python
# File: bookings/views.py

def verify_payment(request):
    data = json.loads(request.body)
    
    payment_id = data.get('razorpay_payment_id')
    order_id = data.get('razorpay_order_id')
    signature = data.get('razorpay_signature')
    booking_id = data.get('booking_id')
    
    # Verify signature
    is_valid = PaymentVerificationService.verify_payment_signature(
        order_id, payment_id, signature
    )
    
    if not is_valid:
        logger.error(f"Invalid signature for order {order_id}")
        return JsonResponse({
            'success': False,
            'error': 'Payment verification failed'
        })
    
    # Confirm booking
    booking = Booking.objects.get(id=booking_id)
    success, error = BookingService.confirm_payment(
        booking, payment_id, signature_verified=True
    )
    
    if success:
        return JsonResponse({
            'success': True,
            'booking_id': booking.id
        })
    else:
        return JsonResponse({
            'success': False,
            'error': error
        })
```

---

## 🧪 Test vs Live Mode

### Test Mode (Development)
```python
# Test credentials (fake payments)
RAZORPAY_KEY_ID = 'rzp_test_xxxxxxxxxxxxx'
RAZORPAY_KEY_SECRET = 'test_secret_key_xxxxx'

# Test card numbers:
# Success: 4111 1111 1111 1111
# Failure: 4000 0000 0000 0002
```

**Benefits:**
- No real money involved
- Can simulate success/failure
- Unlimited test transactions
- Perfect for development

### Live Mode (Production)
```python
# Live credentials (real payments)
RAZORPAY_KEY_ID = 'rzp_live_xxxxxxxxxxxxx'
RAZORPAY_KEY_SECRET = 'live_secret_key_xxxxx'

# Real cards, real money!
# Must complete KYC verification
# Razorpay charges 2% + GST per transaction
```

**Requirements:**
- Complete KYC (business documents)
- Bank account verification
- Live website (HTTPS required)
- Real customers, real money

---

## 🔧 Troubleshooting

### Problem 1: Payment Modal Not Opening
```javascript
// Check if Razorpay script loaded
if (typeof Razorpay === 'undefined') {
    console.error("Razorpay script not loaded!");
    // Add script tag:
    // <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
}

// Check for errors in console
rzp.open();  // Any error messages?
```

### Problem 2: "Order ID not found"
```python
# Make sure order was created and saved to booking
booking = Booking.objects.get(id=booking_id)
if not booking.razorpay_order_id:
    # Order not created yet!
    order_data = create_razorpay_order(booking)
    booking.razorpay_order_id = order_data['order_id']
    booking.save()
```

### Problem 3: Signature Verification Failing
```python
# Check if using correct secret key
print(settings.RAZORPAY_KEY_SECRET)  # Should be test key in development

# Check message format (must be exact!)
message = f"{order_id}|{payment_id}"  # Correct format
# NOT: f"{payment_id}|{order_id}"  # Wrong!

# Try manual verification:
import hmac
import hashlib
expected = hmac.new(
    key=settings.RAZORPAY_KEY_SECRET.encode(),
    msg=message.encode(),
    digestmod=hashlib.sha256
).hexdigest()
print(f"Expected: {expected}")
print(f"Received: {signature}")
```

### Problem 4: Payment Success but Booking Not Confirmed
```python
# Check backend logs
# Look for errors in verify_payment() function

# Check if webhook received (optional)
# Razorpay can send webhook notifications
# Configure in Razorpay dashboard

# Check Razorpay dashboard
# See if payment was actually captured
# Maybe it's in "authorized" state, not "captured"
```

---

## 📊 Razorpay Payment States

```
Order Created → Payment Authorized → Payment Captured → Settled
     ↓                  ↓                  ↓               ↓
  Not Paid         Money on Hold     Money Received   In Bank Account
  (Waiting)        (Pending)         (Success!)       (1-2 days)
```

### State Details

| State | Meaning | Action |
|-------|---------|--------|
| **created** | Order created, waiting for payment | Show payment modal |
| **authorized** | Card charged, money on hold | Capture payment |
| **captured** | Money received by Razorpay | Confirm booking |
| **refund_pending** | Refund initiated | Wait for completion |
| **refunded** | Money returned to customer | Cancel booking |
| **failed** | Payment failed | Show error, retry |

---

## 🎓 Key Takeaways

1. **Payment Gateway = Security**: Never handle card data yourself
2. **Order First**: Create order before showing payment modal
3. **Verify Signature**: Always verify payment signature (security!)
4. **Test Mode**: Use test credentials during development
5. **Error Handling**: Payment can fail, handle it gracefully
6. **Webhooks**: Optional but recommended for reliability
7. **Refunds**: Easy with one API call

---

## 🚀 Next Steps

1. Read: [Understanding Redis](./UNDERSTANDING_REDIS.md) - Learn about caching
2. Read: [Understanding Celery](./UNDERSTANDING_CELERY.md) - Learn about background tasks
3. Practice: Create test orders and payments
4. Explore: Razorpay Dashboard (see all transactions)

---

**Remember**: Razorpay is like a secure cash register - customers pay through it, you get confirmation, nobody sees sensitive card data! 💳🔒

*Last Updated: January 3, 2026*
