# ============================================================================
# 📌 BOOKINGS VIEWS: Core booking and payment workflow
# 
# PURPOSE: Handle all user interactions related to seat selection, booking,
#          and payment processing
#
# KEY CONCEPTS:
# 🎫 BOOKING LIFECYCLE:
#    1. select_seats → User picks seats on UI
#    2. reserve_seats (AJAX) → Seats locked in Redis for 10-12 minutes
#    3. booking_summary → User reviews price and details
#    4. create_booking → PENDING booking saved to database, Razorpay order created
#    5. payment_page → User enters payment details
#    6. payment_success/payment_failed → Razorpay redirects here after payment
#    7. razorpay_webhook → Backup endpoint if user closes browser
#
# 🛡️ SAFETY MECHANISMS:
#    - Redis TTL: Seats auto-released after 12 minutes
#    - Signature Verification: Validate Razorpay payment with secret key
#    - Late Payment Detection: Reject payments that arrive after seat window
#    - Seat Availability Check: Verify no one stole seats during payment
#    - Duplicate Prevention: Use payment_received_at atomic guard
#
# ⚡ REAL-TIME UPDATES:
#    - WebSocket polling via get_seat_status API
#    - Users see updated seat colors as others book/release
#    - 5-second refresh interval for smooth UX
#
# ============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging
from .razorpay_utils import razorpay_client
from .email_utils import send_booking_confirmation_email
from movies.models import Movie
from movies.theater_models import Showtime
from .models import Booking, Transaction
from .utils import SeatManager, PriceCalculator
from django.conf import settings

# 📝 LOGGER: Used to track important events for debugging
# Example: logger.info("Payment received"), logger.error("Seat collision")
logger = logging.getLogger(__name__)

# ==============================================================================
# ❓ THE BOOKING WORKFLOW (Step-by-Step)
# 1. Select Seats: User picks seats on a UI (select_seats).
# 2. Reserve (AJAX): System "locks" them in Redis for 5-10 mins (reserve_seats).
# 3. Summary: User reviews the price and details (booking_summary).
# 4. Create Booking: A "PENDING" record is saved in the Database (create_booking).
# 5. Payment: User enters card details or scans QR (payment_page).
# 6. Confirm: On success, status changes to "CONFIRMED" (mock_payment_success).
# ==============================================================================

# ========== SEAT SELECTION VIEW ==========
# 🎨 PURPOSE: Display interactive seat map for a specific showtime
# 🎨 SECURITY: @login_required decorator ensures only logged-in users access
# 🎨 HOW IT WORKS:
#    1. Get showtime from URL parameter
#    2. Check if showtime is not in the past
#    3. Fetch seat layout, reserved seats, and available seats from Redis
#    4. Mark each seat as: available (green), reserved (yellow), or booked (red)
#    5. Render HTML with interactive seat map
# ========== 

@login_required
def select_seats(request, showtime_id):
    """
    🎨 WHY: This is the interactive part of the booking.
    HOW: We get the movie and time (showtime), and then check Redis to see 
    which seats are already taken. We pass this to the HTML to draw the map.
    """
    showtime = get_object_or_404(Showtime, id=showtime_id, is_active=True)
    
    # Validation: Don't allow booking for movies that already finished.
    if showtime.date < timezone.now().date():
        messages.error(request, 'This showtime has already passed.')
        return redirect('movie_detail', slug=showtime.movie.slug)
    
    # Get seat data from our 'Quick Clipboard' (Redis Cache)
    seat_layout = SeatManager.get_seat_layout(showtime_id)
    reserved_seats = SeatManager.get_reserved_seats(showtime_id)
    available_seats = SeatManager.get_available_seats(showtime_id)
    
    # Logic: Mark each seat as Available, Reserved (locked), or Booked (Sold).
    for row in seat_layout:
        for seat in row:
            if seat:
                if seat['seat_id'] in reserved_seats:
                    seat['status'] = 'reserved'
                elif seat['seat_id'] in available_seats:
                    seat['status'] = 'available'
                else:
                    seat['status'] = 'booked'
    
    context = {
        'showtime': showtime,
        'movie': showtime.movie,
        'seat_layout': seat_layout,
        'screen': showtime.screen,
        'max_seats': 10,
    }
    
    return render(request, 'bookings/select_seats.html', context)

# ========== RESERVE SEATS API (AJAX) ==========
# 💻 JsonResponse: Returns DATA (JSON), not HTML page
# 💻 Used by: Browser JavaScript making AJAX (background) requests
# 💻 PURPOSE: Store seat selection in session before proceeding to payment
# ========== 

@login_required
@csrf_exempt
def reserve_seats(request, showtime_id):
    """
    📝 API ENDPOINT: Store seat selection in user's session
    
    FLOW:
    1. Browser calls this via JavaScript (AJAX)
    2. We save seat_ids to request.session
    3. JavaScript receives { "success": true, "seat_ids": [...] }
    4. User can now proceed to booking summary
    
    WHY SESSION (not Redis yet)?
    - We don't lock seats until user clicks "Proceed to Payment"
    - This is Phase 1 of optimistic locking (just store intent)
    - Real lock happens in create_booking (Phase 2)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        data = json.loads(request.body)
        seat_ids = data.get('seat_ids', [])
        
        if not seat_ids:
            return JsonResponse({'error': 'No seats selected'}, status=400)
        
        if len(seat_ids) > 10:
            return JsonResponse({'error': 'Maximum 10 seats allowed per booking'}, status=400)
        
        # 🟢 OPTIMISTIC LOCKING:
        # We DON'T lock the seats here anymore. We just save the intent in the session.
        # The actual lock will happen when they click "Proceed to Payment".
        reservation = request.session.get('seat_reservation', {})
        reservation[str(showtime_id)] = seat_ids
        request.session['seat_reservation'] = reservation 
        
        return JsonResponse({
            'success': True,
            'message': 'Seats selected',
            'seat_ids': seat_ids
        })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ========== RELEASE SEATS API ==========
@login_required
@csrf_exempt
def release_seats(request, showtime_id):
    """API endpoint to release seats if user cancels selection"""
    try:
        SeatManager.release_seats(showtime_id, user_id=request.user.id)
        # Clear from session too
        reservation = request.session.get('seat_reservation', {})
        if str(showtime_id) in reservation:
            del reservation[str(showtime_id)]
            request.session['seat_reservation'] = reservation
            
        return JsonResponse({'success': True, 'message': 'Seats released'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ========== SEAT STATUS API (for real-time updates) ==========
def get_seat_status(request, showtime_id):
    """
    🔄 API to get current seat status for real-time updates
    Returns: reserved seats (in progress) and booked seats (confirmed)
    """
    try:
        reserved_seats = SeatManager.get_reserved_seats(showtime_id)
        available_seats = SeatManager.get_available_seats(showtime_id)
        
        # Booked seats = all seats - available seats - reserved seats
        seat_layout = SeatManager.get_seat_layout(showtime_id)
        all_seats = []
        for row in seat_layout:
            for seat in row:
                if seat:
                    all_seats.append(seat['seat_id'])
        
        booked_seats = [s for s in all_seats if s not in available_seats and s not in reserved_seats]
        
        return JsonResponse({
            'success': True,
            'reserved_seats': reserved_seats,
            'booked_seats': booked_seats,
            'available_count': len(available_seats)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ========== BOOKING SUMMARY VIEW ==========
@login_required
def booking_summary(request, showtime_id):
    """Review screen before making the final payment"""
    showtime = get_object_or_404(Showtime, id=showtime_id)
    
    # 🕵️ Safety Check: Check session to see if they actually selected seats.
    reservation = request.session.get('seat_reservation', {})
    
    if not reservation or str(showtime_id) not in reservation:
        messages.error(request, 'No seats reserved. Please select seats first.')
        return redirect('select_seats', showtime_id=showtime_id)
    
    seat_ids = reservation[str(showtime_id)]
    
    # Calculate taxes, base price, and total using our utility class.
    price_details = PriceCalculator.calculate_booking_amount(
        showtime, 
        len(seat_ids)
    )
    
    # ⏲️ WHY: UI Synchronization.
    # We pass the exact Redis TTL to the frontend so the user's local timer 
    # stays perfectly in sync with our backend security lock.
    # WHEN: Triggers every time the Summary page is loaded.
    from django.core.cache import cache
    cache_key = f"seat_reservation_{showtime_id}_{request.user.id}"
    remaining_seconds = cache.ttl(cache_key)
    
    context = {
        'showtime': showtime,
        'movie': showtime.movie,
        'seat_ids': seat_ids,
        'seat_count': len(seat_ids),
        'price_details': price_details,
        'total_amount': price_details['total_amount'],
        'expires_in_seconds': remaining_seconds if remaining_seconds > 0 else 600,
    }
    
    return render(request, 'bookings/booking_summary.html', context)

# ========== CREATE BOOKING VIEW ==========
@login_required
@csrf_exempt
def create_booking(request, showtime_id):
    """
    🏗️ WHY: This is the 'Handshake'. 
    The user is ready to pay, so we officially 'Lock' the seats in the database records.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        showtime = get_object_or_404(Showtime, id=showtime_id)
        # 📥 HOW: Get data from the browser (JavaScript)
        data = json.loads(request.body)
        seat_ids = data.get('seat_ids', [])
        
        # 🟢 WHY: Optimistic Locking (Phase 2).
        # We officially 'Lock' the seats in Redis here.
        # HOW: If multiple users try to click 'Pay' at the same millisecond, 
        # Redis (being single-threaded) only lets one 'reserve' successfully.
        # WHEN: Triggers the moment the user clicks the 'Proceed to pay' button.
        success = SeatManager.reserve_seats(showtime_id, seat_ids, request.user.id)
        
        if not success:
             # 🕵️ LOG: This is a race condition event. 
             # Useful for debugging if many users complain about 'stolen' seats.
             print(f"⚠️ SAFETY CHECK FAILED: User {request.user.id} tried to book seats {seat_ids} for showtime {showtime_id} but they were already taken.")
             return JsonResponse({
                 'success': False,
                 'error': 'Oh no! One or more of these seats were just taken by another user.'
             }, status=400)
        
        price_details = PriceCalculator.calculate_booking_amount(showtime, len(seat_ids))
        
        # Save to SQL Database (Permanent Record)
        booking = Booking.objects.create(
            user=request.user,
            showtime=showtime,
            seats=seat_ids,
            total_seats=len(seat_ids),
            base_price=price_details['base_price'],
            convenience_fee=price_details['convenience_fee'],
            tax_amount=price_details['tax_amount'],
            total_amount=price_details['total_amount'],
            status='PENDING'
        )
        
        # 💳 WHY: Payment Initiation.
        # We skip separate landing pages and pop the modal directly for a 'One-Click' feel.
        # HOW: This function receives order data from our 'create-booking' API and opens Razorpay.
        # WHEN: Triggers after the backend confirms seats are successfully reserved in Redis.
        order_data = razorpay_client.create_order(
            amount=booking.total_amount,
            receipt=f"booking_{booking.booking_number}"
        )
        
        if not order_data['success']:
            # If Razorpay fails, we still have the 'PENDING' booking, but we can't pay yet.
            return JsonResponse({
                'success': False, 
                'error': f"Payment Gateway Error: {order_data['error']}"
            }, status=500)

        # 🔗 SYNC: Save the order ID to the booking record for verification later.
        # WHY: Security Anchor. This ensures we only accept a success response
        # that specifically matches this created order, preventing payment hijacking.
        # WHEN: Triggers immediately after Razorpay confirms order creation.
        # 🔐 ALSO: Record when payment was initiated for timeout checks
        booking.razorpay_order_id = order_data['order_id']
        booking.payment_initiated_at = timezone.now()
        booking.save()

        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
            'booking_number': booking.booking_number,
            'total_amount': float(booking.total_amount),
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'order_id': order_data['order_id'],
            'amount': order_data['amount'],
            'currency': order_data['currency'],
            'is_mock': order_data.get('is_mock', False),
            'redirect_url': f'/bookings/{booking.id}/payment/' # Fallback
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def payment_page(request, booking_id):
    """Show the payment landing page with a countdown timer and Razorpay integration."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # 🕵️ Cleanup: If user takes too long to pay, expire the booking.
    if booking.is_expired():
        booking.status = 'EXPIRED'
        booking.save()
        # Free the seats so other users can book them.
        SeatManager.release_seats(booking.showtime.id, booking.seats)
        messages.error(request, 'Payment window expired. Please try again.')
        return redirect('select_seats', showtime_id=booking.showtime.id)
    
    # 💳 HOW: Create Razorpay Order
    # We send the amount and receipt to Razorpay API to get an 'order_id'.
    # ❓ WHY: This creates a single source of truth for this payment attempt.
    # It prevents double-charging and allows us to track this specific transaction on Razorpay's dashboard.
    order_data = razorpay_client.create_order(
        amount=booking.total_amount,
        receipt=f"booking_{booking.booking_number}"
    )
    
    if not order_data['success']:
        # 🛡️ WHY: Fail gracefully. If the gateway is down, we don't want a 500 error.
        messages.error(request, f"Payment Gateway Error: {order_data['error']}")
        return redirect('booking_summary', showtime_id=booking.showtime.id)

    context = {
        'booking': booking,
        'movie': booking.showtime.movie,
        'showtime': booking.showtime,
        # ⏱️ WHY: UX - Let the user know they have a limited window to pay before seats are released.
        'time_remaining': int((booking.expires_at - timezone.now()).total_seconds()) if booking.expires_at else 0,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order_data['order_id'],
        'amount': order_data['amount'],
        'currency': order_data['currency'],
        'is_mock': order_data.get('is_mock', False),
    }
    
    return render(request, 'bookings/payment.html', context)

@login_required
def payment_success(request, booking_id):
    """
    🎉 PAYMENT SUCCESS HANDLER: Called after Razorpay confirms payment
    
    FLOW:
    1. Razorpay redirects user to this URL with payment details
    2. We extract payment_id, order_id, and signature from URL
    3. Verify signature using Razorpay secret key (prevents forgery)
    4. Check if order_id matches our database (prevents payment hijacking)
    5. Check if payment arrived before seat window expired (prevents late payments)
    6. Check if seats still available (prevents booking collision)
    7. Mark booking as CONFIRMED and send confirmation email
    
    🛡️ CRITICAL GUARDS:
    - Signature verification: Ensures Razorpay sent this, not attacker
    - Order ID matching: Ensures payment is for this specific booking
    - Expiration check: Ensures payment arrived in time
    - Seat availability check: Ensures no one stole seats during payment
    - Atomic guard: payment_received_at prevents duplicate processing
    """
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Get parameters from Razorpay redirect
    razorpay_payment_id = request.GET.get('razorpay_payment_id')
    razorpay_order_id = request.GET.get('razorpay_order_id')
    razorpay_signature = request.GET.get('razorpay_signature')
    
    # 🕵️ SECURITY: Ensure the Order ID matches our database anchor.
    # WHY: Authority Model. Even if Razorpay's modal stays open too long, 
    # our DB is the final judge of whether this specific order is still valid.
    # WHEN: Triggers on the redirect from Razorpay success page.
    if razorpay_order_id != booking.razorpay_order_id:
        messages.error(request, 'Payment mismatch. Please contact support.')
        return redirect('my_bookings')

    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        messages.error(request, 'Invalid payment response received.')
        return redirect('payment_page', booking_id=booking.id)
    
    # 🔐 CRITICAL SECURITY: Verify the signature
    is_valid = razorpay_client.verify_payment_signature(
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature
    )
    
    if is_valid:
        # � PAYMENT TIMEOUT CHECK: Ensure payment arrived BEFORE expiration
        # WHY: Seats are released after 12 minutes, payment after that is invalid
        # HOW: Compare payment_received_at with booking.expires_at
        payment_received_at = timezone.now()
        
        if payment_received_at > booking.expires_at:
            # 💰 LATE PAYMENT: Booking expired before payment was received
            # ✅ Payment WAS successful, but booking window closed
            time_diff = (payment_received_at - booking.expires_at).total_seconds()
            
            booking.status = 'FAILED'
            booking.payment_id = razorpay_payment_id
            booking.payment_received_at = payment_received_at
            booking.save()
            
            logger.warning(
                f"⏰ LATE PAYMENT DETECTED: {booking.booking_number}\n"
                f"   ✅ Payment received at: {payment_received_at}\n"
                f"   ❌ Window expired at: {booking.expires_at}\n"
                f"   ⏱️  Lateness: {time_diff:.1f} seconds over deadline\n"
                f"   💳 Payment ID: {razorpay_payment_id}\n"
                f"   👤 User: {request.user.username}\n"
                f"   📊 Status set to: FAILED\n"
                f"   📧 Action: Refund email queued"
            )
            
            # Send refund email (Async Celery task) - Only if not already sent
            if not booking.refund_notification_sent:
                from .email_utils import send_late_payment_email
                task = send_late_payment_email.delay(booking.id)
                logger.info(f"📧 Late payment refund email task queued: {task.id}")
            else:
                logger.info(f"⏭️  Refund email already sent for booking {booking.booking_number}")
            
            messages.error(
                request, 
                f'⏰ Payment window expired ({int(time_diff)} seconds late). Your seats were released. '
                'Refund will be processed within 24 hours. Check your email for details.'
            )
            return redirect('select_seats', showtime_id=booking.showtime.id)
        
        # �🕵️ THE POST-PAYMENT SAFETY SHIELD:
        # One last check to see if anyone stole the seats during the payment window.
        # WHY: Data Authority. Client-side clocks (Razorpay modal) can stay open 
        # longer than our server-side safety lock. This is the master check.
        # HOW: We re-query the database for any 'CONFIRMED' tickets that might 
        # have been issued during the small gap between Redis expiry and Payment success.
        # WHEN: Triggers after Razorpay signals success but before we commit the ticket.
        is_still_valid = SeatManager.is_seat_still_available_for_user(
            booking.showtime.id, 
            booking.seats, 
            request.user.id
        )
        
        if not is_still_valid:
            # 🚨 DISASTER RECOVERY: The seat was taken while they were paying.
            # 1. Mark booking as FAILED
            booking.status = 'FAILED'
            booking.payment_id = razorpay_payment_id
            booking.save()
            
            # 2. LOG it
            print(f"❌ BOOKING COLLISION: Payment received for {booking.booking_number} but seats were taken!")
            
            # 3. Inform user (In a real app, you'd trigger a Razorpay refund here)
            messages.error(request, 'Oh no! The seats were taken while you were paying. We have initiated an automatic refund.')
            return redirect('my_bookings')

        # ✅ ALL CLEAR: Proceed with confirmation
        # 🛡️ CRITICAL: Set payment_received_at FIRST (atomic guard)
        # Once payment_received_at is set, no failure email will ever be sent
        # This is the critical protection against race conditions
        payment_received_at = timezone.now()
        booking.payment_received_at = payment_received_at
        booking.payment_id = razorpay_payment_id
        booking.payment_method = 'RAZORPAY'
        booking.status = 'CONFIRMED'
        booking.confirmed_at = timezone.now()
        booking.save()
        
        # Confirm seats in Redis (after atomic transaction)
        SeatManager.confirm_seats(booking.showtime.id, booking.seats)
        
        # Send confirmation email (Async) - only after status is CONFIRMED
        from .email_utils import send_booking_confirmation_email
        send_booking_confirmation_email.delay(booking.id)
        
        messages.success(request, 'Ticket booked successfully!')
        return redirect('booking_detail', booking_id=booking.id)
    else:
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('my_bookings')

@login_required
def payment_failed(request, booking_id):
    """Handle payment cancellation or failure"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # 🛡️ CRITICAL: Check if payment actually succeeded
    # If payment_received_at is set, payment succeeded - don't send failure email
    if booking.payment_received_at:
        logger.info(
            f"⏭️ payment_failed view called for {booking.booking_number}, "
            f"but payment_received_at is set. Redirecting to success page."
        )
        messages.success(request, 'Ticket booked successfully!')
        return redirect('booking_detail', booking_id=booking.id)
    
    # Reload fresh from DB to check current state
    booking.refresh_from_db()
    
    # Double-check: payment might have succeeded in the meantime
    if booking.payment_received_at:
        logger.info(
            f"⏭️ After refresh, payment_received_at is set for {booking.booking_number}. "
            f"Payment succeeded, not sending failure email."
        )
        messages.success(request, 'Ticket booked successfully!')
        return redirect('booking_detail', booking_id=booking.id)
    
    # Only mark as FAILED if not already in a terminal state
    if booking.status == 'PENDING':
        booking.status = 'FAILED'
        booking.failure_email_sent = False  # Reset flag before saving
        booking.save()
        
        # Send payment failed email (Async) - only if not already sent
        if not booking.failure_email_sent:
            from .email_utils import send_payment_failed_email
            send_payment_failed_email.delay(booking.id)
    
    messages.error(request, 'Payment was unsuccessful. Your seats have been released.')
    return redirect('select_seats', showtime_id=booking.showtime.id)

# ============================================================================
# 📌 RAZORPAY WEBHOOK ENDPOINT
# PURPOSE: Background notification handler from Razorpay payment gateway
# WHY: Users might close browser before returning from Razorpay, so we need
#      Razorpay to notify us directly about payment status
# ============================================================================
@csrf_exempt
def razorpay_webhook(request):
    """
    🤖 WEBHOOK HANDLER: Receives payment notifications from Razorpay
    
    TRIGGERS WHEN:
    1. User completes payment but closes browser before redirect
    2. Payment confirmed on Razorpay side
    3. Razorpay automatically notifies our endpoint
    
    SECURITY:
    - csrf_exempt: Razorpay doesn't have CSRF token, so we exempt this endpoint
    - In production, verify webhook signature to ensure it's really Razorpay
    
    LATE PAYMENT CHECK:
    - Validate that payment arrived before booking window expired
    - If expired: Reject payment and queue refund email
    - If valid: Confirm booking and send confirmation email
    """
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        webhook_body = request.body.decode('utf-8')
        webhook_data = json.loads(webhook_body)
        
        event = webhook_data.get('event', '')
        payload = webhook_data.get('payload', {})
        payment_entity = payload.get('payment', {}).get('entity', {})
        
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        
        if event == 'payment.captured':
            try:
                booking = Booking.objects.get(razorpay_order_id=order_id)
                payment_received_at = timezone.now()
                
                # 🔐 CHECK: Is payment too late?
                if payment_received_at > booking.expires_at:
                    # ⏰ LATE PAYMENT: Booking expired, reject this payment
                    # ✅ Payment WAS successful, but booking window closed
                    time_diff = (payment_received_at - booking.expires_at).total_seconds()
                    
                    booking.status = 'FAILED'
                    booking.payment_id = payment_id
                    booking.payment_received_at = payment_received_at
                    booking.save()
                    
                    logger.warning(
                        f"⏰ WEBHOOK LATE PAYMENT DETECTED: {booking.booking_number}\n"
                        f"   ✅ Payment received at: {payment_received_at}\n"
                        f"   ❌ Window expired at: {booking.expires_at}\n"
                        f"   ⏱️  Lateness: {time_diff:.1f} seconds over deadline\n"
                        f"   💳 Payment ID: {payment_id}\n"
                        f"   📊 Status set to: FAILED\n"
                        f"   📧 Action: Refund email queued"
                    )
                    
                    # Send refund email (Async Celery task) - Only if not already sent
                    if not booking.refund_notification_sent:
                        from .email_utils import send_late_payment_email
                        task = send_late_payment_email.delay(booking.id)
                        logger.info(f"📧 Late payment refund email task queued via webhook: {task.id}")
                    else:
                        logger.info(f"⏭️  Refund email already sent for booking {booking.booking_number} via webhook")
                    
                    return HttpResponse(status=200)
                
                # ✅ VALID: Payment is on time
                # Only confirm if not already confirmed (to avoid double emails)
                if booking.status == 'PENDING':
                    # 🛡️ CRITICAL: Check if payment_received_at is already set
                    # (payment_success view beat us to it)
                    booking.refresh_from_db()
                    
                    if booking.payment_received_at:
                        logger.info(f"⏭️  WEBHOOK: Booking {booking.booking_number} already has payment_received_at. Skipping.")
                        return HttpResponse(status=200)
                    
                    # Set all fields
                    booking.payment_received_at = payment_received_at
                    booking.payment_id = payment_id
                    booking.status = 'CONFIRMED'
                    booking.confirmed_at = timezone.now()
                    booking.save()
                    
                    SeatManager.confirm_seats(booking.showtime.id, booking.seats)
                    
                    # Send confirmation email (email task has idempotency checks)
                    from .email_utils import send_booking_confirmation_email
                    send_booking_confirmation_email.delay(booking.id)
                    logger.info(f"✅ WEBHOOK: Confirmation email task queued for booking {booking.booking_number}")
                elif booking.status == 'CONFIRMED':
                    # Already confirmed by payment_success view - don't process again
                    logger.info(f"⏭️  WEBHOOK: Booking {booking.booking_number} already confirmed. Skipping.")
                else:
                    # Booking in some other state - don't process
                    logger.info(f"⏭️  WEBHOOK: Booking {booking.booking_number} is {booking.status}. Skipping.")
            except Booking.DoesNotExist:
                logger.error(f"⚠️ Webhook: Booking not found for order {order_id}")
                pass
                
        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return HttpResponse(status=400)

@login_required
def my_bookings(request):
    """
    📜 WHY: History - Users need to see their past and upcoming tickets.
    """
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'bookings': bookings,
        'now': timezone.now(),
    }
    
    return render(request, 'bookings/my_bookings.html', context)

@login_required
def booking_detail(request, booking_id):
    """
    🎫 WHY: Digital Ticket - This is the actual ticket the user shows at the theater.
    """
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    context = {
        'booking': booking,
        'movie': booking.showtime.movie,
        'showtime': booking.showtime,
        'theater': booking.showtime.screen.theater,
    }
    
    return render(request, 'bookings/booking_detail.html', context)

# ========== CANCEL BOOKING API ==========
@login_required
@csrf_exempt
def cancel_booking_api(request, booking_id):
    """
    🚫 WHY: Cancel a PENDING booking and release seats immediately
    Used when:
    1. User refreshes the summary page
    2. User closes Razorpay modal (payment abandoned)
    3. User explicitly cancels booking
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        
        # Only cancel PENDING bookings
        if booking.status != 'PENDING':
            return JsonResponse({
                'success': False,
                'error': f'Cannot cancel booking with status: {booking.status}'
            }, status=400)
        
        # 🛡️ CRITICAL CHECK: If payment was already received, don't cancel
        # This prevents sending failure email after successful payment
        if booking.payment_received_at:
            return JsonResponse({
                'success': False,
                'error': 'Payment already received - booking cannot be cancelled',
                'booking_id': booking.id
            }, status=400)
        
        # Reload fresh from DB to double-check
        booking.refresh_from_db()
        if booking.payment_received_at:
            return JsonResponse({
                'success': False,
                'error': 'Payment already received - booking cannot be cancelled',
                'booking_id': booking.id
            }, status=400)
        
        # Get reason from request
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', 'User cancelled booking')
        showtime_id = booking.showtime.id  # Always use the booking's showtime
        
        # 🛡️ Mark as FAILED (payment was abandoned/cancelled)
        # WHY: This differentiates from user-requested cancellations vs payment failures
        booking.status = 'FAILED'
        booking.failure_email_sent = False  # Reset flag before saving
        booking.save()
        
        # Send payment failed email (Async) - Modal was closed/abandoned
        # Email task itself has idempotency checks, but we still call it
        from .email_utils import send_payment_failed_email
        send_payment_failed_email.delay(booking.id)
        
        # 🛡️ CRITICAL: Release seats from Redis using the BOOKING's seats
        # WHY: We must pass the actual seat_ids, not just user_id, to ensure proper cleanup
        SeatManager.release_seats(showtime_id, booking.seats, request.user.id)
        
        # Clear session reservation data
        if 'seat_reservation' in request.session:
            reservation = request.session['seat_reservation']
            if str(showtime_id) in reservation:
                del reservation[str(showtime_id)]
                request.session['seat_reservation'] = reservation
        
        logger.info(
            f"Booking {booking.booking_number} marked as FAILED by user {request.user.id}. "
            f"Reason: {reason}. Seats released: {booking.seats}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Booking cancelled and seats released',
            'booking_id': booking.id,
            'seats_released': booking.seats
        })
        
    except Exception as e:
        logger.error(f"Error cancelling booking {booking_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ========== BEACON-FRIENDLY SEAT RELEASE API ==========
@csrf_exempt
def release_booking_beacon(request, booking_id):
    """
    🚨 EMERGENCY RELEASE: Handle tab close via navigator.sendBeacon()
    
    WHY: When user force-closes tab (Cmd+W), JavaScript ondismiss doesn't fire.
    sendBeacon() is the only reliable way to send data during page unload.
    
    SECURITY: This endpoint is csrf_exempt but validates booking ownership
    via the booking ID which is only known to the booking creator.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        # Parse the beacon data
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', 'Tab closed (beacon)')
        
        # Get booking - don't require login since beacon may not have session
        booking = Booking.objects.filter(id=booking_id, status='PENDING').first()
        
        if not booking:
            # Booking doesn't exist, already processed, or already confirmed - that's OK
            return HttpResponse(status=200)
        
        # 🛡️ CRITICAL CHECK: If payment was already received, don't send failure email
        # This prevents race condition where payment success is being processed
        # while beacon is also being sent
        if booking.payment_received_at:
            logger.info(
                f"BEACON IGNORED: Booking {booking.booking_number} already has payment_received_at. "
                f"Payment confirmation is in progress - not sending failure email."
            )
            return HttpResponse(status=200)
        
        # Mark as FAILED and release seats (only if still PENDING)
        booking.status = 'FAILED'
        booking.failure_email_sent = False  # Reset flag before saving
        booking.save()
        
        # Send payment failed email (Async) - Tab was closed during payment
        from .email_utils import send_payment_failed_email
        send_payment_failed_email.delay(booking.id)
        
        SeatManager.release_seats(booking.showtime.id, booking.seats, booking.user.id)
        
        logger.info(
            f"BEACON: Booking {booking.booking_number} released. "
            f"Reason: {reason}. Seats: {booking.seats}"
        )
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Beacon release error for booking {booking_id}: {e}")
        return HttpResponse(status=200)  # Return 200 anyway - beacon can't retry

