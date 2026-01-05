# Add this function to add_sample_data.py
def create_sample_bookings():
    """Create sample bookings for testing"""
    from bookings.models import Booking
    from django.contrib.auth.models import User
    from movies.models import Showtime
    
    # Get a user
    user = User.objects.first()
    if not user:
        print("No user found. Please create a user first.")
        return
    
    # Get a showtime
    showtime = Showtime.objects.first()
    if not showtime:
        print("No showtime found. Please create showtimes first.")
        return
    
    # Create sample bookings
    bookings_data = [
        {
            'user': user,
            'showtime': showtime,
            'seats': ['A1', 'A2', 'A3'],
            'status': 'CONFIRMED',
        },
        {
            'user': user,
            'showtime': showtime,
            'seats': ['B4', 'B5'],
            'status': 'PENDING',
        },
    ]
    
    for booking_data in bookings_data:
        booking = Booking.objects.create(**booking_data)
        print(f"Created booking: {booking.booking_number}")
    
    print("✓ Created sample bookings")

# Call this function in your main function