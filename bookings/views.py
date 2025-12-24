from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .razorpay_utils import razorpay_client
from .email_utils import send_booking_confirmation_email
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from movies.models import Movie
from movies.theater_models import Showtime
from .models import Booking, Transaction
from .utils import SeatManager, PriceCalculator
from .razorpay_utils import razorpay_client
from django.conf import settings

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
# ❓ JsonResponse: 
# Instead of returning a full HTML page, this returns DATA (JSON).
# This is used for AJAX requests (background calls) from the Browser's JavaScript.
@login_required
@csrf_exempt
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
    
    context = {
        'showtime': showtime,
        'movie': showtime.movie,
        'seat_ids': seat_ids,
        'seat_count': len(seat_ids),
        'price_details': price_details,
        'total_amount': price_details['total_amount'],
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
        
        # 🟢 WHY: Optimistic Locking.
        # We check one last time if the seats are still free.
        # If two people click at the same time, only one will succeed here.
        success = SeatManager.reserve_seats(showtime_id, seat_ids, request.user.id)
        
        if not success:
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
        
        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
            'booking_number': booking.booking_number,
            'total_amount': float(booking.total_amount),
            'redirect_url': f'/bookings/{booking.id}/payment/'
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
    }
    
    return render(request, 'bookings/payment.html', context)

@login_required
def payment_success(request, booking_id):
    """Callback view for Razorpay success"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # 📥 HOW: Razorpay sends these IDs back to us after the user pays.
    payment_id = request.GET.get('razorpay_payment_id')
    order_id = request.GET.get('razorpay_order_id')
    signature = request.GET.get('razorpay_signature')
    
    # 🔐 WHY: SECURITY (Signature Verification). 
    # NEVER trust the frontend URL parameters alone! A hacker could manually type '/success/'
    # into the browser. We must verify the HMAC signature using our 'SECRET_KEY' to prove 
    # that this success message actually came from Razorpay.
    is_valid = razorpay_client.verify_payment_signature(order_id, payment_id, signature)
    
    if is_valid:
        # 🛠️ HOW: Atomic Update.
        # Check if status is still PENDING to avoid 'Replay Attacks' (submitting success twice).
        if booking.status == 'PENDING':
            booking.status = 'CONFIRMED'
            booking.payment_method = 'RAZORPAY'
            booking.payment_id = payment_id
            booking.confirmed_at = timezone.now()
            booking.save()
            
            # 🔨 HOW: Confirm seats permanently in Redis.
            SeatManager.confirm_seats(booking.showtime.id, booking.seats)
            
            # ✉️ WHY: Asynchronous Task.
            # Sending emails takes 2-3 seconds. If we did it here, the user's browser would 'hang'.
            # By using .delay(), we push it to Celery and return the response to the user INSTANTLY.
            from .email_utils import send_booking_confirmation_email
            send_booking_confirmation_email.delay(booking.id)
            
            messages.success(request, 'Payment successful! Your booking is confirmed.')
        return redirect('booking_detail', booking_id=booking.id)
    else:
        # 🚫 WHY: If verification fails, it's a security risk or data corruption.
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('payment_failed', booking_id=booking.id)

@login_required
def payment_failed(request, booking_id):
    """View shown when payment fails"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'bookings/payment_failed.html', {'booking': booking})

# ========== MY BOOKINGS & DETAILS ==========
@login_required
def my_bookings(request):
    """Show history of all tickets bought by the user."""
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})

@login_required
def booking_detail(request, booking_id):
    """Digital ticket view with movie time, seats, and theater info."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'bookings/booking_detail.html', {
        'booking': booking,
        'movie': booking.showtime.movie,
        'showtime': booking.showtime,
        'theater': booking.showtime.screen.theater,
    })


@login_required
def initiate_payment(request, booking_id):
    boking=get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status !='PENDING':
        messages.error(request, f"Booking is already {booking.status.lower()}")
        return redirect('booking_detail', booking_id=booking.id)
    
    order_data=razorpay_client.create_order(
        amount=float(booking.total_amount),
        receipt=f"{booking.booking_number}",

    )
    if not order_data['success']:
        messages.erroe(request, "Payment failed!! Please try again.")
        return redirect('booking_detail', booking_id=booking.id)

    # Save order ID to booking
    booking.razorpay_order_id = order_data['order_id']
    booking.save()
    
    context = {
        'booking': booking,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order_data['order_id'],
        'amount': order_data['amount'],
        'currency': order_data['currency'],
        'user': {
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'contact': '',  # Add phone field to user model if needed
        }
    }

    return render(request, 'bookings/razorpay_payment.html', context)
# ========== PAYMENT SUCCESS CALLBACK ==========
@login_required
def payment_success(request, booking_id):
    """Handle successful payment callback"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Get payment details from request
    razorpay_payment_id = request.GET.get('razorpay_payment_id')
    razorpay_order_id = request.GET.get('razorpay_order_id')
    razorpay_signature = request.GET.get('razorpay_signature')
    
    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        messages.error(request, 'Invalid payment response')
        return redirect('payment_page', booking_id=booking.id)
    
    # Verify payment signature
    is_valid = razorpay_client.verify_payment_signature(
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature
    )
    
    if not is_valid:
        messages.error(request, 'Payment verification failed')
        return redirect('payment_page', booking_id=booking.id)
    
    # Mark booking as confirmed
    booking.mark_as_confirmed(razorpay_payment_id)
    
    messages.success(request, 'Payment successful! Booking confirmed.')
    return redirect('booking_detail', booking_id=booking.id)

# ========== PAYMENT FAILED CALLBACK ==========
@login_required
def payment_failed(request, booking_id):
    """Handle failed payment callback"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Mark booking as failed
    booking.mark_as_failed()
    
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('payment_page', booking_id=booking.id)

# ========== RAZORPAY WEBHOOK ==========
@csrf_exempt
def razorpay_webhook(request):
    """Handle Razorpay webhook for payment updates"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        # Get webhook data
        webhook_body = request.body.decode('utf-8')
        webhook_data = json.loads(webhook_body)
        
        # Verify webhook signature (important for production)
        received_signature = request.headers.get('X-Razorpay-Signature', '')
        
        # For now, we'll trust the webhook (in production, verify signature)
        event = webhook_data.get('event', '')
        payload = webhook_data.get('payload', {})
        payment = payload.get('payment', {})
        entity = payment.get('entity', {})
        
        payment_id = entity.get('id')
        order_id = entity.get('order_id')
        status = entity.get('status')
        
        # Find booking by order_id
        try:
            booking = Booking.objects.get(razorpay_order_id=order_id)
            
            if event == 'payment.captured' and status == 'captured':
                # Payment successful
                booking.mark_as_confirmed(payment_id)
                print(f"Webhook: Payment captured for booking {booking.booking_number}")
                
            elif event == 'payment.failed':
                # Payment failed
                booking.mark_as_failed()
                print(f"Webhook: Payment failed for booking {booking.booking_number}")
                
        except Booking.DoesNotExist:
            print(f"Webhook: No booking found for order {order_id}")
        
        return HttpResponse(status=200)
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return HttpResponse(status=400)


