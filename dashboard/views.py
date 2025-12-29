from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json
import csv
from django.http import HttpResponse
from bookings.models import Booking, Transaction
from movies.models import Movie
from movies.theater_models import Showtime, Theater
from django.contrib.auth.models import User

from django.conf import settings
import django

# ========== ANALYTICS DASHBOARD ==========
@staff_member_required
def analytics_dashboard(request):
    """Main analytics dashboard view.

    WHY: Serves the container HTML for the single-page application (SPA) style dashboard.
    HOW: Renders `admin/dashboard/analytics.html` which loads the Chart.js library and our custom `dashboard.js`.
    WHEN: Accessed by admin staff via `/admin/dashboard/`.
    """
    return render(request, 'admin/dashboard/analytics.html')

# ========== API ENDPOINTS FOR CHARTS ==========
@staff_member_required
def revenue_data(request):
    """API endpoint for revenue and booking trends.

    WHY: The frontend needs raw JSON data to render the Line Chart for revenue and bookings over time.
    HOW: Aggregates `Booking` records by date for the last 30 days and by week for the last 4 weeks.
    WHEN: Called via AJAX by `dashboard.js` when the dashboard loads or refreshes.
    """
    # Get date range (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Generate dates
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Get daily revenue
    daily_revenue = []
    daily_bookings = []
    
    # HOW: Iterate through each date to build a consistent timeline.
    # This ensures that days with 0 revenue still appear on the chart (as flat lines),
    # rather than jumping gaps in dates.
    for date_str in dates:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # WHY: Aggregate revenue for this specific date.
        # Filter: Only count 'CONFIRMED' bookings to ensure accuracy.
        # Aggregate: Sum the 'total_amount' field.
        day_revenue = Booking.objects.filter(
            created_at__date=date_obj,
            status='CONFIRMED'
        ).aggregate(total=Sum('total_amount'))['total'] or 0  # Handle None result
        
        # WHY: Count total valid bookings for the same date.
        day_bookings = Booking.objects.filter(
            created_at__date=date_obj,
            status='CONFIRMED'
        ).count()
        
        # Store as float for JSON serialization
        daily_revenue.append(float(day_revenue))
        daily_bookings.append(day_bookings)

    
    # Get weekly revenue
    weekly_revenue = []
    weekly_labels = []
    
    for i in range(4):  # Last 4 weeks
        week_start = end_date - timedelta(days=(i+1)*7)
        week_end = end_date - timedelta(days=i*7)
        
        week_total = Booking.objects.filter(
            created_at__date__range=[week_start, week_end],
            status='CONFIRMED'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        weekly_revenue.append(float(week_total))
        weekly_labels.append(f'Week {i+1}')
    
    # Get top movies
    top_movies = Movie.objects.annotate(
        booking_count=Count('showtime__booking'),
        total_revenue=Sum('showtime__booking__total_amount')
    ).filter(
        booking_count__gt=0
    ).order_by('-total_revenue')[:5]
    
    movie_data = []
    for movie in top_movies:
        movie_data.append({
            'title': movie.title[:20] + ('...' if len(movie.title) > 20 else ''),
            'revenue': float(movie.total_revenue or 0),
            'bookings': movie.booking_count,
            'rating': movie.rating,
        })
    
    return JsonResponse({
        'dates': dates,
        'daily_revenue': daily_revenue,
        'daily_bookings': daily_bookings,
        'weekly_revenue': weekly_revenue,
        'weekly_labels': weekly_labels,
        'top_movies': movie_data,
    })

@staff_member_required
def user_activity_data(request):
    """API endpoint for user growth and activity.

    WHY: Visualizes user acquisition (new signups) vs. retention (active bookers).
    HOW: Queries `User` model for `date_joined` and `Booking` model for distinct users per day.
    WHEN: Fetched by the frontend to populate the 'User Activity' chart.
    """
    # New users per day (last 7 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)
    
    dates = []
    new_users = []
    active_users = []
    
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%b %d'))
        
        # New users
        new_count = User.objects.filter(
            date_joined__date=current_date
        ).count()
        new_users.append(new_count)
        
        # Active users (users who booked)
        active_count = Booking.objects.filter(
            created_at__date=current_date
        ).values('user').distinct().count()
        active_users.append(active_count)
        
        current_date += timedelta(days=1)
    
    # User demographics
    total_users = User.objects.count()
    active_today = Booking.objects.filter(
        created_at__date=end_date
    ).values('user').distinct().count()
    
    return JsonResponse({
        'dates': dates,
        'new_users': new_users,
        'active_users': active_users,
        'total_users': total_users,
        'active_today': active_today,
    })

@staff_member_required
def movie_performance_data(request):
    """API endpoint for top performing movies.

    WHY: Helps admins identify which movies are driving revenue and tickets.
    HOW: Annotates `Movie` objects with sum of `booking__total_amount` and count of bookings.
    WHEN: Used to render the 'Top Movies' bar chart and pie charts.
    """
    # Movies by bookings
    movies = Movie.objects.annotate(
        booking_count=Count('showtime__booking')
    ).filter(
        booking_count__gt=0
    ).order_by('-booking_count')[:10]
    
    movie_labels = [movie.title[:15] + ('...' if len(movie.title) > 15 else '') for movie in movies]
    booking_counts = [movie.booking_count for movie in movies]
    
    # Movies by revenue
    revenue_movies = Movie.objects.annotate(
        total_revenue=Sum('showtime__booking__total_amount')
    ).filter(
        total_revenue__isnull=False
    ).order_by('-total_revenue')[:5]
    
    revenue_labels = [movie.title[:15] + ('...' if len(movie.title) > 15 else '') for movie in revenue_movies]
    revenue_amounts = [float(movie.total_revenue or 0) for movie in revenue_movies]
    
    # Genre distribution
    from movies.models import Genre
    genre_stats = []
    genres = Genre.objects.all()
    
    for genre in genres:
        movie_count = Movie.objects.filter(genres=genre, is_active=True).count()
        if movie_count > 0:
            genre_stats.append({
                'genre': genre.name,
                'count': movie_count,
            })
    
    return JsonResponse({
        'movie_labels': movie_labels,
        'booking_counts': booking_counts,
        'revenue_labels': revenue_labels,
        'revenue_amounts': revenue_amounts,
        'genre_stats': genre_stats,
    })

@staff_member_required
def theater_performance_data(request):
    """API endpoint for theater occupancy and revenue.

    WHY: Critical for analyzing which theaters are underperforming or overperforming.
    HOW: Calculates occupancy rate (sold seats / total seats) and total revenue per theater.
    WHEN: Displayed in the 'Theater Performance' table or chart on the dashboard.
    """
    theaters = Theater.objects.annotate(
        total_bookings=Count('screen__showtime__booking'),
        total_revenue=Sum('screen__showtime__booking__total_amount'),
        avg_occupancy=Sum('screen__showtime__booking__total_seats') * 100 / Sum('screen__total_seats')
    ).filter(
        total_bookings__gt=0
    ).order_by('-total_revenue')
    
    theater_data = []
    for theater in theaters:
        theater_data.append({
            'name': theater.name,
            'city': theater.city.name,
            'bookings': theater.total_bookings or 0,
            'revenue': float(theater.total_revenue or 0),
            'occupancy': float(theater.avg_occupancy or 0),
        })
    
    return JsonResponse({'theaters': theater_data})

@staff_member_required
def realtime_stats(request):
    """API endpoint for live system heartbeat.

    WHY: specialized for "right now" metrics like pending bookings and today's total revenue.
    HOW: Queries for bookings made in the last 5 minutes.
    WHEN: Polled every 30 seconds by `dashboard.js` to show live updates without refreshing.
    """
    now = timezone.now()
    today = now.date()
    
    # Pending bookings (last 5 minutes)
    pending_bookings = Booking.objects.filter(
        status='PENDING',
        created_at__gte=now - timedelta(minutes=5)
    ).count()
    
    # Today's stats
    today_stats = {
        'confirmed': Booking.objects.filter(
            created_at__date=today,
            status='CONFIRMED'
        ).count(),
        'pending': Booking.objects.filter(
            created_at__date=today,
            status='PENDING'
        ).count(),
        'failed': Booking.objects.filter(
            created_at__date=today,
            status='FAILED'
        ).count(),
        'revenue': float(Booking.objects.filter(
            created_at__date=today,
            status='CONFIRMED'
        ).aggregate(total=Sum('total_amount'))['total'] or 0),
    }
    
    # Recent activity
    recent_bookings = Booking.objects.select_related(
        'user', 'showtime__movie'
    ).order_by('-created_at')[:5]
    
    recent_activity = []
    for booking in recent_bookings:
        recent_activity.append({
            'type': 'booking',
            'user': booking.user.username,
            'movie': booking.showtime.movie.title,
            'amount': float(booking.total_amount),
            'status': booking.status,
            'time': booking.created_at.strftime('%H:%M'),
        })
    
    return JsonResponse({
        'pending_now': pending_bookings,
        'today': today_stats,
        'recent_activity': recent_activity,
        'timestamp': now.strftime('%H:%M:%S'),
    })

# ========== REPORT GENERATION ==========
@staff_member_required
def export_bookings_csv(request):
    """Generate CSV export of booking references.

    WHY: Allows staff to perform offline analysis or accounting in Excel/Sheets.
    HOW: Streams a CSV response with headers and booking rows, filtered by optional date range.
    WHEN: Triggered when user clicks 'Export Bookings' button.
    """
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Filter bookings
    bookings = Booking.objects.select_related(
        'user', 'showtime__movie', 'showtime__screen__theater'
    ).order_by('-created_at')
    
    if start_date and end_date:
        bookings = bookings.filter(
            created_at__date__range=[start_date, end_date]
        )
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bookings_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Booking ID', 'Date', 'User', 'Movie', 'Theater',
        'Showtime', 'Seats', 'Amount', 'Status', 'Payment Method'
    ])
    
    for booking in bookings:
        writer.writerow([
            booking.booking_number,
            booking.created_at.strftime('%Y-%m-%d %H:%M'),
            booking.user.username,
            booking.showtime.movie.title,
            booking.showtime.screen.theater.name,
            f"{booking.showtime.date} {booking.showtime.start_time}",
            ', '.join(booking.seats) if isinstance(booking.seats, list) else booking.seats,
            booking.total_amount,
            booking.status,
            booking.payment_method or 'N/A',
        ])
    
    return response

@staff_member_required
def export_revenue_report(request):
    """Export revenue report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="revenue_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Total Bookings', 'Confirmed', 'Failed', 'Revenue', 'Avg Ticket Price'])
    
    # Last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    current_date = start_date
    while current_date <= end_date:
        day_bookings = Booking.objects.filter(created_at__date=current_date)
        total = day_bookings.count()
        confirmed = day_bookings.filter(status='CONFIRMED').count()
        failed = day_bookings.filter(status='FAILED').count()
        revenue = day_bookings.filter(status='CONFIRMED').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        avg_price = revenue / confirmed if confirmed > 0 else 0
        
        writer.writerow([
            current_date.strftime('%Y-%m-%d'),
            total,
            confirmed,
            failed,
            revenue,
            round(avg_price, 2)
        ])
        
        current_date += timedelta(days=1)
    
    return response

# ========== SYSTEM MONITORING ==========
@staff_member_required
def system_status(request):
    """Health check endpoint for critical infrastructure.

    WHY: One-stop shop to verify if DB, Redis, Email, and Celery are operational.
    HOW: Attempts a simple operation (ping/select 1) on each service and catches exceptions.
    WHEN: Loaded on the 'System Health' tab of the dashboard.
    """
    import redis
    from django.db import connection
    import smtplib
    
    status = {
        'database': False,
        'redis': False,
        'email': False,
        'celery': False,
    }
    
    messages = []
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['database'] = True
        messages.append({'type': 'success', 'message': 'Database connected'})
    except Exception as e:
        messages.append({'type': 'error', 'message': f'Database error: {str(e)}'})
    
    # Check Redis
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        status['redis'] = True
        messages.append({'type': 'success', 'message': 'Redis connected'})
    except Exception as e:
        messages.append({'type': 'error', 'message': f'Redis error: {str(e)}'})
    
    # Check email
    try:
        if settings.EMAIL_HOST:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=5)
            server.starttls()
            server.quit()
            status['email'] = True
            messages.append({'type': 'success', 'message': 'Email server reachable'})
        else:
            messages.append({'type': 'warning', 'message': 'Email not configured'})
    except Exception as e:
        messages.append({'type': 'error', 'message': f'Email error: {str(e)}'})
    
    # Check Celery (simplified check)
    try:
        from celery import current_app
        insp = current_app.control.inspect()
        if insp.active():
            status['celery'] = True
            messages.append({'type': 'success', 'message': 'Celery workers active'})
        else:
            messages.append({'type': 'warning', 'message': 'No active Celery workers'})
    except Exception as e:
        messages.append({'type': 'error', 'message': f'Celery error: {str(e)}'})
    
    # System info
    import psutil
    import platform
    
    system_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'django_version': django.get_version(),
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
    }
    
    return JsonResponse({
        'status': status,
        'messages': messages,
        'system_info': system_info,
    })