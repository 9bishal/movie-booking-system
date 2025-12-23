from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from movies.models import Movie
from movies.theater_models import Showtime
from .models import Booking, Transaction
from .utils import SeatManager, PriceCalculator

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
    """Show seat selection interface"""
    showtime = get_object_or_404(Showtime, id=showtime_id, is_active=True)
    
    # 🕵️ Validation: Don't allow booking for movies that already finished.
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
    """API endpoint to reserve seats"""
    if request.method != 'POST':#mean if request is not post then return error
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        data = json.loads(request.body)
        seat_ids = data.get('seat_ids', [])
        
        if not seat_ids:
            return JsonResponse({'error': 'No seats selected'}, status=400)
        
        # Security: Prevent single users from grabbing too many seats.
        if len(seat_ids) > 10:
            return JsonResponse({'error': 'Maximum 10 seats allowed per booking'}, status=400)
        
        # Try to lock seats in Redis
        success = SeatManager.reserve_seats(showtime_id, seat_ids, request.user.id)
        
        if success:
            # 💡 Tip: Store the selection in the session so the next page knows what you picked.
            reservation = request.session.get('seat_reservation', {})
            reservation[str(showtime_id)] = seat_ids
            request.session['seat_reservation'] = reservation 
            
            return JsonResponse({
                'success': True,
                'message': f'{len(seat_ids)} seats reserved for 5 minutes',
                'seat_ids': seat_ids,
                'reservation_time': 300, 
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Some seats are no longer available. Someone else might have grabbed them!'
            }, status=400)
            
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
    """Final step: Create the 'PENDING' record in the Database."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        showtime = get_object_or_404(Showtime, id=showtime_id)
        data = json.loads(request.body)
        seat_ids = data.get('seat_ids', [])
        
        # 🕵️ Race Condition Check: Are the seats STILL held for this user in Redis?
        # This prevents session manipulation hacks.
        reserved_seats = SeatManager.get_reserved_seats(showtime_id)
        for seat_id in seat_ids:
            if seat_id not in reserved_seats:
                return JsonResponse({'error': 'Seats no longer reserved'}, status=400)
        
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

# ========== PAYMENT VIEW ==========
@login_required
def payment_page(request, booking_id):
    """Show the payment landing page with a countdown timer."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # 🕵️ Cleanup: If user takes too long to pay, expire the booking.
    if booking.is_expired():
        booking.status = 'EXPIRED'
        booking.save()
        # Free the seats so other users can book them.
        SeatManager.release_seats(booking.showtime.id, booking.seats)
        messages.error(request, 'Payment window expired. Please try again.')
        return redirect('select_seats', showtime_id=booking.showtime.id)
    
    context = {
        'booking': booking,
        'movie': booking.showtime.movie,
        'showtime': booking.showtime,
        'time_remaining': int((booking.expires_at - timezone.now()).total_seconds()) if booking.expires_at else 0,
    }
    
    return render(request, 'bookings/payment.html', context)

# ========== MOCK PAYMENT SUCCESS ==========
# In a real app, this would be a callback/webhook from Stripe or Razorpay.
@login_required
def mock_payment_success(request, booking_id):
    """Simulate a successful payment for testing."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status == 'PENDING':
        booking.status = 'CONFIRMED'
        booking.payment_method = 'MOCK'
        booking.payment_id = f"MOCK-{int(timezone.now().timestamp())}"
        booking.confirmed_at = timezone.now()
        booking.save()
        
        # 🔑 CRITICAL: Once paid, mark seats as BOOKED (permanent)
        SeatManager.confirm_seats(booking.showtime.id, booking.seats)
        
        messages.success(request, f'Booking confirmed! Enjoy your movie.')
    
    return redirect('booking_detail', booking_id=booking.id)

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