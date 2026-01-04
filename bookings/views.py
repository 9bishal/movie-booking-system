from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging
from .razorpay_utils import razorpay_client
from .email_utils import send_booking_confirmation_email
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from movies.models import Movie
from movies.theater_models import Showtime
from .models import Booking, Transaction
from .utils import SeatManager, PriceCalculator
from django.conf import settings
from utils.rate_limit import booking_limiter
from utils.performance import PerformanceMonitor

# Initialize logger
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
# ❓ @login_required: 
# This is a Django Decorator. It ensures that only logged-in users can access this page.
# Anonymous users will be redirected to the login page automatically.

@booking_limiter.rate_limit_view
@login_required
@PerformanceMonitor.measure_performance
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
# ❓ JsonResponse: 
# Instead of returning a full HTML page, this returns DATA (JSON).
# This is used for AJAX requests (background calls) from the Browser's JavaScript.
@login_required
@csrf_exempt
@booking_limiter.rate_limit_view
def reserve_seats(request, showtime_id):
    """API endpoint to store seat selection in session (Optimistic Locking Phase 1)"""
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

# ========== BOOKING SUMMARY VIEW ==========
@login_required
def booking_summary(request, showtime_id):
    """Review screen before making the final payment"""
    showtime = get_object_or_404(Showtime, id=showtime_id)
    
    # Check if user already has a PENDING booking for this showtime
    # This will be passed to client-side JS for refresh detection
    existing_booking = Booking.objects.filter(
        user=request.user,
        showtime=showtime,
        status='PENDING'
    ).first()
    
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
        'booking': existing_booking,  # For client-side refresh detection
    }
    
    return render(request, 'bookings/booking_summary.html', context)

# ========== CREATE BOOKING VIEW ==========
@login_required
@csrf_exempt
@booking_limiter.rate_limit_view
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
        #WHY: Security Anchor. This ensures we only accept a success response
        #that specifically matches this created order, preventing payment hijacking.
        #WHEN: Triggers immediately after Razorpay confirms order creation.
        booking.razorpay_order_id = order_data['order_id']
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
    from .email_utils import send_payment_failed_email
    
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # 🕵️ Cleanup: If user takes too long to pay, expire the booking.
    if booking.is_expired():
        booking.status = 'EXPIRED'
        booking.save()
        # Free the seats so other users can book them.
        SeatManager.release_seats(booking.showtime.id, booking.seats)
        
        # Send payment failed/expired email
        try:
            send_payment_failed_email.delay(booking.id)
            logger.info(f"📧 Booking expired email task queued for {booking.booking_number}")
        except Exception as e:
            logger.warning(f"⚠️ Celery not available, sending expired email synchronously: {e}")
            try:
                send_payment_failed_email(booking.id)
                logger.info(f"📧 Booking expired email sent synchronously for {booking.booking_number}")
            except Exception as email_error:
                logger.error(f"❌ Failed to send expired email: {email_error}")
        
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
    🎉 PAYMENT SUCCESS HANDLER
    
    WHAT HAPPENS:
    1. User completes Razorpay payment
    2. Razorpay redirects to this view
    3. We verify the payment signature (security check)
    4. Update booking status to CONFIRMED in database
    5. Send confirmation email via Celery
    6. Redirect to booking ticket page
    
    WHY: Razorpay redirects here after a successful transaction.
    HOW: We verify the signature to ENSURE the payment was real.
    """
    from .email_utils import send_booking_confirmation_email
    
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
        # 🕵️ THE POST-PAYMENT SAFETY SHIELD:
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
            logger.error(f"❌ BOOKING COLLISION: Payment received for {booking.booking_number} but seats were taken!")
            
            # 3. Inform user (In a real app, you'd trigger a Razorpay refund here)
            messages.error(request, 'Oh no! The seats were taken while you were paying. We have initiated an automatic refund.')
            return redirect('my_bookings')

        # ✅ ALL CLEAR: Proceed with confirmation
        
        # ========== STEP 1: UPDATE DATABASE IMMEDIATELY ==========
        # Change booking status from PENDING to CONFIRMED
        # This is a PERMANENT change saved to database
        booking.status = 'CONFIRMED'
        booking.payment_id = razorpay_payment_id  # Save Razorpay payment ID
        booking.confirmed_at = timezone.now()  # Record when payment was confirmed
        booking.payment_method = 'RAZORPAY'  # Record payment method
        booking.save()  # ← SAVE TO DATABASE NOW (immediate)
        
        logger.info(f"✅ Booking {booking.booking_number} confirmed. Payment ID: {razorpay_payment_id}")
        
        # ========== STEP 2: MARK SEATS AS PERMANENTLY BOOKED ==========
        # Move seats from "reserved temporarily" to "confirmed permanently" in Redis
        # Other users can no longer book these seats
        SeatManager.confirm_seats(booking.showtime.id, booking.seats)
        
        # ========== STEP 3: SEND CONFIRMATION EMAIL (ASYNC) ==========
        # Queue email sending task with Celery
        # .delay() sends it to background worker - user doesn't wait
        # Email contains booking details + QR code
        try:
            # Try async with Celery (preferred)
            send_booking_confirmation_email.delay(booking.id)
            logger.info(f"📧 Email task queued for booking {booking.booking_number}")
        except Exception as e:
            # Fallback: Send synchronously if Celery is not running
            logger.warning(f"⚠️ Celery not available, sending email synchronously: {e}")
            try:
                send_booking_confirmation_email(booking.id)
                logger.info(f"📧 Email sent synchronously for booking {booking.booking_number}")
            except Exception as email_error:
                logger.error(f"❌ Failed to send email: {email_error}")
        
        # ========== STEP 4: SHOW SUCCESS MESSAGE ==========
        # Display green success message to user
        messages.success(
            request,
            f'✅ Ticket booked successfully! Booking: {booking.booking_number}. Check your email for confirmation.'
        )
        
        # ========== STEP 5: REDIRECT TO TICKET PAGE ==========
        # User is automatically sent to their booking details page
        # They can see their ticket with QR code
        return redirect('booking_detail', booking_id=booking.id)
    
    else:
        # ❌ PAYMENT VERIFICATION FAILED
        # This means payment signature doesn't match - possible fraud
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('my_bookings')

@login_required
def payment_failed(request, booking_id):
    """
    ❌ HANDLE PAYMENT FAILURE OR CANCELLATION
    
    WHEN: User cancels payment or payment fails
    WHAT: Mark booking as FAILED and release seats
    """
    from .email_utils import send_payment_failed_email
    
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Update booking status to FAILED
    booking.status = 'FAILED'
    booking.save()  # Save to database
    
    # Send payment failed email
    try:
        # Try async with Celery (preferred)
        send_payment_failed_email.delay(booking.id)
        logger.info(f"📧 Payment failed email task queued for booking {booking.booking_number}")
    except Exception as e:
        # Fallback: Send synchronously if Celery is not running
        logger.warning(f"⚠️ Celery not available, sending payment failed email synchronously: {e}")
        try:
            send_payment_failed_email(booking.id)
            logger.info(f"📧 Payment failed email sent synchronously for booking {booking.booking_number}")
        except Exception as email_error:
            logger.error(f"❌ Failed to send payment failed email: {email_error}")
    
    # Inform user
    messages.error(request, 'Payment was unsuccessful. Your seats have been released.')
    
    # Take user back to seat selection page
    return redirect('select_seats', showtime_id=booking.showtime.id)

@csrf_exempt
def razorpay_webhook(request):
    """
    🤖 WHY: Background notification from Razorpay.
    If the user closes their browser before returning to 'payment_success', 
    Razorpay tells the server directly via this webhook.
    """
    from .email_utils import send_booking_confirmation_email
    
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
                if booking.status != 'CONFIRMED':
                    booking.status = 'CONFIRMED'
                    booking.payment_id = payment_id
                    booking.confirmed_at = timezone.now()
                    booking.save()
                    SeatManager.confirm_seats(booking.showtime.id, booking.seats)
                    
                    # Send confirmation email via webhook
                    try:
                        send_booking_confirmation_email.delay(booking.id)
                        logger.info(f"📧 Email task queued via webhook for booking {booking.booking_number}")
                    except Exception as e:
                        logger.warning(f"⚠️ Celery not available in webhook, sending email synchronously: {e}")
                        try:
                            send_booking_confirmation_email(booking.id)
                            logger.info(f"📧 Email sent synchronously via webhook for booking {booking.booking_number}")
                        except Exception as email_error:
                            logger.error(f"❌ Failed to send email via webhook: {email_error}")
            except Booking.DoesNotExist:
                pass
                
        return HttpResponse(status=200)
    except Exception as e:
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
    2. User closes Razorpay modal
    3. User explicitly cancels booking
    """
    from .email_utils import send_payment_failed_email
    
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
        
        # Get reason from request
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', 'User cancelled booking')
        showtime_id = data.get('showtime_id', booking.showtime.id)
        
        # Cancel the booking
        booking.status = 'CANCELLED'
        booking.save()
        
        # Release seats from Redis
        SeatManager.release_seats(showtime_id, booking.seats, request.user.id)
        
        # Clear session
        if 'seat_reservation' in request.session:
            reservation = request.session['seat_reservation']
            if str(showtime_id) in reservation:
                del reservation[str(showtime_id)]
                request.session['seat_reservation'] = reservation
        
        # Send cancellation email (using payment_failed template)
        try:
            send_payment_failed_email.delay(booking.id)
            logger.info(f"📧 Booking cancelled email task queued for {booking.booking_number}")
        except Exception as e:
            logger.warning(f"⚠️ Celery not available, sending cancelled email synchronously: {e}")
            try:
                send_payment_failed_email(booking.id)
                logger.info(f"📧 Booking cancelled email sent synchronously for {booking.booking_number}")
            except Exception as email_error:
                logger.error(f"❌ Failed to send cancelled email: {email_error}")
        
        logger.info(
            f"Booking {booking.booking_number} cancelled by user {request.user.id}. "
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




