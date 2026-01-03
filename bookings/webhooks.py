"""
🔔 RAZORPAY WEBHOOK HANDLER
WHY: Async payment confirmations from Razorpay
WHAT: Receives and processes payment.captured, payment.failed events
WHEN: Called by Razorpay servers after payment status changes
"""

import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Booking, Transaction
from .services import BookingService, PaymentVerificationService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """
    🔔 WEBHOOK ENDPOINT: Receives payment notifications from Razorpay
    
    WHY: Razorpay sends async notifications about payment status
    HOW: Verify signature, find booking, update status
    WHEN: Called by Razorpay servers (not user browser)
    
    IMPORTANT: Must be idempotent (safe to receive same event multiple times)
    """
    try:
        # Step 1: Get webhook payload
        payload = request.body.decode('utf-8')
        signature = request.headers.get('X-Razorpay-Signature', '')
        
        logger.info(f"Received webhook: {payload[:100]}...")  # Log first 100 chars
        
        # Step 2: Verify webhook signature (CRITICAL for security)
        is_valid, error = PaymentVerificationService.verify_webhook_signature(payload, signature)
        if not is_valid:
            logger.warning(f"Invalid webhook signature: {error}")
            return HttpResponse('Invalid signature', status=400)
        
        # Step 3: Parse webhook data
        webhook_data = json.loads(payload)
        event = webhook_data.get('event', '')
        
        logger.info(f"Processing webhook event: {event}")
        
        # Step 4: Route to appropriate handler
        if event == 'payment.captured':
            return handle_payment_captured(webhook_data)
        
        elif event == 'payment.failed':
            return handle_payment_failed(webhook_data)
        
        elif event == 'payment.authorized':
            return handle_payment_authorized(webhook_data)
        
        else:
            logger.info(f"Unhandled webhook event: {event}")
            return HttpResponse('Event not handled', status=200)
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {str(e)}")
        return HttpResponse('Invalid JSON', status=400)
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return HttpResponse('Internal error', status=500)


def handle_payment_captured(webhook_data):
    """
    ✅ PAYMENT SUCCESS: Handle payment.captured event
    
    WHY: Razorpay confirms payment was successful
    HOW: Find booking by order_id, confirm payment
    WHEN: After user successfully pays
    """
    try:
        payload = webhook_data.get('payload', {})
        payment_entity = payload.get('payment', {}).get('entity', {})
        
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        amount = payment_entity.get('amount', 0) / 100  # Convert paise to rupees
        status = payment_entity.get('status')
        
        logger.info(f"Payment captured: order_id={order_id}, payment_id={payment_id}, amount={amount}")
        
        # Find booking by Razorpay order ID
        try:
            booking = Booking.objects.get(razorpay_order_id=order_id)
        except Booking.DoesNotExist:
            logger.error(f"Booking not found for order_id: {order_id}")
            return HttpResponse('Booking not found', status=404)
        
        # Idempotent check - already confirmed?
        if booking.status == 'CONFIRMED':
            logger.info(f"Booking {booking.booking_number} already confirmed. Skipping webhook processing.")
            return HttpResponse('Already processed', status=200)
        
        # Verify amount matches
        if float(booking.total_amount) != amount:
            logger.warning(
                f"Amount mismatch for booking {booking.booking_number}: "
                f"expected {booking.total_amount}, got {amount}"
            )
            # Don't fail - log and proceed (Razorpay is source of truth)
        
        # Confirm payment using service layer
        success, error = BookingService.confirm_payment(
            booking=booking,
            payment_id=payment_id,
            signature_verified=True  # Webhook signature already verified
        )
        
        if success:
            # Create transaction record
            Transaction.objects.create(
                booking=booking,
                transaction_id=payment_id,
                amount=amount,
                status='SUCCESS',
                payment_gateway='RAZORPAY',
                gateway_response=payment_entity
            )
            
            logger.info(f"Payment confirmed via webhook for booking {booking.booking_number}")
            return HttpResponse('Payment confirmed', status=200)
        else:
            logger.error(f"Failed to confirm payment: {error}")
            return HttpResponse(f'Confirmation failed: {error}', status=500)
    
    except Exception as e:
        logger.error(f"Error handling payment.captured: {str(e)}")
        return HttpResponse('Internal error', status=500)


def handle_payment_failed(webhook_data):
    """
    ❌ PAYMENT FAILED: Handle payment.failed event
    
    WHY: Razorpay notifies that payment failed
    HOW: Find booking, mark as FAILED, release seats
    WHEN: After payment fails (card declined, etc.)
    """
    try:
        payload = webhook_data.get('payload', {})
        payment_entity = payload.get('payment', {}).get('entity', {})
        
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        error_description = payment_entity.get('error_description', 'Unknown error')
        
        logger.info(f"Payment failed: order_id={order_id}, payment_id={payment_id}, error={error_description}")
        
        # Find booking
        try:
            booking = Booking.objects.get(razorpay_order_id=order_id)
        except Booking.DoesNotExist:
            logger.error(f"Booking not found for failed payment: {order_id}")
            return HttpResponse('Booking not found', status=404)
        
        # Only update if still pending
        if booking.status == 'PENDING':
            booking.status = 'FAILED'
            booking.payment_id = payment_id
            booking.save()
            
            # Release seats
            from .utils import SeatManager
            SeatManager.release_seats(booking.showtime.id, booking.seats)
            
            # Create transaction record
            Transaction.objects.create(
                booking=booking,
                transaction_id=payment_id,
                amount=booking.total_amount,
                status='FAILED',
                payment_gateway='RAZORPAY',
                gateway_response=payment_entity
            )
            
            # Send failure email (optional)
            from .email_utils import send_payment_failed_email
            send_payment_failed_email.delay(booking.id)
            
            logger.info(f"Booking {booking.booking_number} marked as FAILED")
        else:
            logger.info(f"Booking {booking.booking_number} status is {booking.status}, not updating")
        
        return HttpResponse('Payment failure recorded', status=200)
    
    except Exception as e:
        logger.error(f"Error handling payment.failed: {str(e)}")
        return HttpResponse('Internal error', status=500)


def handle_payment_authorized(webhook_data):
    """
    🔒 PAYMENT AUTHORIZED: Handle payment.authorized event
    
    WHY: Payment captured but not yet settled
    HOW: Log event, optionally update booking
    WHEN: For some payment methods (UPI, etc.)
    
    NOTE: Usually we wait for payment.captured
    """
    try:
        payload = webhook_data.get('payload', {})
        payment_entity = payload.get('payment', {}).get('entity', {})
        
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        
        logger.info(f"Payment authorized: order_id={order_id}, payment_id={payment_id}")
        
        # Optionally update booking status to "AUTHORIZED" (if you have this status)
        # For now, just log and wait for payment.captured
        
        return HttpResponse('Payment authorized', status=200)
    
    except Exception as e:
        logger.error(f"Error handling payment.authorized: {str(e)}")
        return HttpResponse('Internal error', status=500)


@csrf_exempt
@require_POST
def payment_callback(request):
    """
    🔄 PAYMENT CALLBACK: Receives payment response from user's browser
    
    WHY: User redirected here after payment (success or failure)
    HOW: Verify signature, confirm payment, redirect to booking detail
    WHEN: Called by user's browser after Razorpay modal closes
    
    NOTE: Webhook is more reliable, but callback provides better UX
    """
    try:
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            logger.warning("Missing payment callback parameters")
            return HttpResponse('Missing parameters', status=400)
        
        logger.info(f"Payment callback: order_id={razorpay_order_id}, payment_id={razorpay_payment_id}")
        
        # Find booking
        try:
            booking = Booking.objects.get(razorpay_order_id=razorpay_order_id)
        except Booking.DoesNotExist:
            logger.error(f"Booking not found for order_id: {razorpay_order_id}")
            return HttpResponse('Booking not found', status=404)
        
        # Verify signature
        is_valid, error = PaymentVerificationService.verify_payment_signature(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        )
        
        if not is_valid:
            logger.warning(f"Invalid payment signature in callback: {error}")
            booking.status = 'FAILED'
            booking.save()
            return HttpResponse('Invalid signature', status=400)
        
        # Confirm payment
        success, error = BookingService.confirm_payment(
            booking=booking,
            payment_id=razorpay_payment_id,
            signature_verified=True
        )
        
        if success:
            logger.info(f"Payment confirmed via callback for booking {booking.booking_number}")
            # Redirect to success page
            from django.shortcuts import redirect
            return redirect('booking_detail', booking_id=booking.id)
        else:
            logger.error(f"Failed to confirm payment via callback: {error}")
            return HttpResponse(f'Confirmation failed: {error}', status=500)
    
    except Exception as e:
        logger.error(f"Error handling payment callback: {str(e)}")
        return HttpResponse('Internal error', status=500)
