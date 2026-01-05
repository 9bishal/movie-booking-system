from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking
from movies.models import Movie
from movies.theater_models import Showtime
from django.contrib.auth.models import User

def admin_stats(request):
    """Add admin statistics to all admin templates"""
    if not request.user.is_staff:
        return {}
    
    try:
        # Today's date
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Today's bookings
        today_bookings = Booking.objects.filter(
            created_at__date=today
        )
        
        # Yesterday's bookings for comparison
        yesterday_bookings = Booking.objects.filter(
            created_at__date=yesterday
        )
        
        # Calculate stats
        stats = {
            # Counts
            'total_bookings_today': today_bookings.count(),
            'total_bookings_yesterday': yesterday_bookings.count(),
            
            # Revenue
            'revenue_today': sum(b.total_amount for b in today_bookings.filter(status='CONFIRMED')),
            'revenue_yesterday': sum(b.total_amount for b in yesterday_bookings.filter(status='CONFIRMED')),
            
            # Growth
            'booking_growth': calculate_growth(today_bookings.count(), yesterday_bookings.count()),
            'revenue_growth': calculate_growth(
                sum(b.total_amount for b in today_bookings.filter(status='CONFIRMED')),
                sum(b.total_amount for b in yesterday_bookings.filter(status='CONFIRMED'))
            ),
            
            # User stats
            'total_users': User.objects.count(),
            'new_users_today': User.objects.filter(date_joined__date=today).count(),
            
            # Movie stats
            'total_movies': Movie.objects.filter(is_active=True).count(),
            'active_showtimes': Showtime.objects.filter(is_active=True, date__gte=today).count(),
        }
        
        return {'admin_stats': stats}
        
    except Exception as e:
        # Don't break admin if stats fail
        print(f"Stats error: {e}")
        return {'admin_stats': {}}

def calculate_growth(today_value, yesterday_value):
    """Calculate percentage growth"""
    if yesterday_value == 0:
        return 100 if today_value > 0 else 0
    return round(((today_value - yesterday_value) / yesterday_value) * 100, 1)