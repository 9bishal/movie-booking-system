# dashboard/context_processors.py
# ------------------------------------------------------------
# This module provides context processors for the admin dashboard.
# The `admin_stats` function injects key statistics into the template
# context for staff users. It is only executed for admin (staff) users
# and returns an empty dict for regular users.
# ------------------------------------------------------------

from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking
from movies.models import Movie
from movies.theater_models import Showtime
from django.contrib.auth.models import User

def admin_stats(request):
    """Collect admin statistics for the dashboard.

    WHY: Staff need a quick overview of the system's health – bookings,
    revenue, user growth, and movie/showtime activity – to make informed
    decisions and spot issues early.
    HOW: Query the database for today and yesterday aggregates, compute
    growth percentages, and assemble them into a dictionary that Django
    injects into the template context.
    WHEN: Django calls this context processor automatically during the
    rendering of any template that includes it (e.g., the admin dashboard
    pages). It runs on each request, ensuring the displayed metrics are
    up‑to‑date.
    """
    # Only staff users should see these stats; otherwise return an empty dict.
    if not hasattr(request, 'user') or not request.user.is_staff:
        return {}
    
    try:
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        # Bookings for today and yesterday
        today_bookings = Booking.objects.filter(created_at__date=today)
        yesterday_bookings = Booking.objects.filter(created_at__date=yesterday)

        # Assemble statistics
        stats = {
            # Counts
            'total_bookings_today': today_bookings.count(),
            'total_bookings_yesterday': yesterday_bookings.count(),
            # Revenue (only CONFIRMED bookings count towards revenue)
            'revenue_today': sum(b.total_amount for b in today_bookings.filter(status='CONFIRMED')),
            'revenue_yesterday': sum(b.total_amount for b in yesterday_bookings.filter(status='CONFIRMED')),
            # Growth percentages
            'booking_growth': calculate_growth(today_bookings.count(), yesterday_bookings.count()),
            'revenue_growth': calculate_growth(
                sum(b.total_amount for b in today_bookings.filter(status='CONFIRMED')),
                sum(b.total_amount for b in yesterday_bookings.filter(status='CONFIRMED'))
            ),
            # User statistics
            'total_users': User.objects.count(),
            'new_users_today': User.objects.filter(date_joined__date=today).count(),
            # Movie and showtime statistics
            'total_movies': Movie.objects.filter(is_active=True).count(),
            'active_showtimes': Showtime.objects.filter(is_active=True, date__gte=today).count(),
        }
        return {'admin_stats': stats}
    except Exception as e:
        # Log the error for debugging; in production you might use proper logging.
        print(f"Error in admin_stats context processor: {e}")
        return {'admin_stats': {}}


def calculate_growth(today_value, yesterday_value):
    """Calculate percentage growth between two values.

    WHY: Growth metrics give staff a sense of momentum (e.g., bookings are
    increasing week over week).
    HOW: Avoid division‑by‑zero; if yesterday's value is zero, treat any
    positive today value as 100% growth.
    WHEN: Used internally by `admin_stats` when assembling the context.
    """
    if yesterday_value == 0:
        return 100 if today_value > 0 else 0
    return round(((today_value - yesterday_value) / yesterday_value) * 100, 1)
