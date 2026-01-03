from django.urls import path
from . import views
from . import webhooks  # NEW: Webhook handlers

urlpatterns = [
    # Seat Selection
    path('select-seats/<int:showtime_id>/', views.select_seats, name='select_seats'),
    
    # AJAX Reservation
    path('api/reserve-seats/<int:showtime_id>/', views.reserve_seats, name='reserve_seats'),
    path('api/release-seats/<int:showtime_id>/', views.release_seats, name='release_seats'),
    # path('api/check-seats/<int:showtime_id>/', views.check_seat_availability, name='check_seat_availability'),
    
    # Booking Summary
    path('summary/<int:showtime_id>/', views.booking_summary, name='booking_summary'),
    
    # Create Booking
    path('api/create-booking/<int:showtime_id>/', views.create_booking, name='create_booking'),
    
    # Cancel Booking
    path('cancel/<int:booking_id>/', views.cancel_booking_api, name='cancel_booking_api'),
    
    # Payment Flow
    path('<int:booking_id>/payment/', views.payment_page, name='payment_page'),
    path('<int:booking_id>/payment/success/', views.payment_success, name='payment_success'),
    path('<int:booking_id>/payment/failed/', views.payment_failed, name='payment_failed'),
    
    # 🔔 NEW: Webhook endpoints
    path('webhooks/razorpay/', webhooks.razorpay_webhook, name='razorpay_webhook'),
    path('webhooks/payment-callback/', webhooks.payment_callback, name='payment_callback'),
    
    # My Bookings
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('detail/<int:booking_id>/', views.booking_detail, name='booking_detail'),
]