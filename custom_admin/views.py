"""
Custom Admin Dashboard Views

This module provides authentication and API endpoints for the custom admin dashboard.
All views are protected with @staff_member_required decorator to ensure only staff members
can access the dashboard and its data.

Features:
- Custom login/logout (not Django admin)
- Beautiful admin dashboard with real-time analytics
- RESTful API endpoints for dashboard data
- Chart.js integration for data visualization
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from bookings.models import Booking
from movies.models import Movie
from movies.theater_models import Theater


# ============= AUTHENTICATION VIEWS =============

def admin_login(request):
    """
    Custom admin login page.
    
    Handles staff member authentication. Only users with is_staff=True can login.
    Redirects authenticated staff to dashboard.
    
    GET: Display login form
    POST: Authenticate user credentials
    
    Returns: 
        - Redirect to dashboard if already logged in
        - Login template if GET request or authentication fails
        - Redirect to dashboard if authentication successful
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('custom_admin:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('custom_admin:dashboard')
        else:
            return render(request, 'custom_admin/login.html', {
                'error': 'Invalid credentials or not a staff member'
            })
    
    return render(request, 'custom_admin/login.html')


@login_required(login_url='custom_admin:login')
def admin_logout(request):
    """
    Custom admin logout handler.
    
    Logs out the current user and redirects to login page.
    Only accessible to authenticated users.
    
    Returns:
        Redirect to login page
    """
    if request.user.is_staff:
        logout(request)
    return redirect('custom_admin:login')


# ============= DASHBOARD VIEWS =============

@staff_member_required(login_url='custom_admin:login')
def dashboard(request):
    """
    Main admin dashboard page.
    
    Displays the custom admin dashboard with charts and analytics.
    Dashboard data is loaded asynchronously via JavaScript API calls.
    
    Access: Only staff members
    
    Returns:
        HTML dashboard template with user context
    """
    return render(request, 'custom_admin/dashboard.html')


# ============= API ENDPOINTS =============
# All API endpoints return JSON and require staff authentication
# Used by JavaScript dashboard to fetch real-time data

@staff_member_required(login_url='custom_admin:login')
@require_http_methods(["GET"])
def api_stats(request):
    """
    Get summary statistics for dashboard stat cards.
    
    Calculates:
    - Total revenue from confirmed bookings (all time)
    - Today's revenue from confirmed bookings
    - Total booking count (all time)
    - Today's booking count
    
    Returns:
        JSON: {
            "total_revenue": float,
            "today_revenue": float,
            "total_bookings": int,
            "today_bookings": int
        }
    """
    today = timezone.now().date()
    
    # Calculate total revenue from all confirmed bookings
    total_revenue = Booking.objects.filter(
        status='CONFIRMED'
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Calculate today's revenue
    today_revenue = Booking.objects.filter(
        created_at__date=today,
        status='CONFIRMED'
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Count total bookings
    total_bookings = Booking.objects.filter(status='CONFIRMED').count()
    
    # Count today's bookings
    today_bookings = Booking.objects.filter(
        created_at__date=today,
        status='CONFIRMED'
    ).count()
    
    return JsonResponse({
        'total_revenue': float(total_revenue),
        'today_revenue': float(today_revenue),
        'total_bookings': total_bookings,
        'today_bookings': today_bookings,
    })


@staff_member_required(login_url='custom_admin:login')
@require_http_methods(["GET"])
def api_revenue(request):
    """
    Get daily revenue data for the last N days.
    
    Used to render the revenue trend line chart on dashboard.
    Returns daily revenue totals for each date in the range.
    
    Query Parameters:
        days (int): Number of days to fetch (default: 30)
    
    Returns:
        JSON: {
            "dates": ["2025-12-10", "2025-12-11", ...],
            "revenues": [0.0, 2500.0, ...]
        }
    """
    # Get number of days from query parameter (default: 30)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    dates = []
    revenues = []
    
    # Iterate through each day and calculate revenue
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        
        # Sum revenue for this day
        daily_revenue = Booking.objects.filter(
            created_at__date=current_date,
            status='CONFIRMED'
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        revenues.append(float(daily_revenue))
        current_date += timedelta(days=1)
    
    return JsonResponse({
        'dates': dates,
        'revenues': revenues,
    })


@staff_member_required(login_url='custom_admin:login')
@require_http_methods(["GET"])
def api_bookings(request):
    """
    Get top movies and recent bookings data.
    
    Calculates:
    1. Top 5 movies by number of confirmed bookings
    2. 5 most recent confirmed bookings with user and movie details
    
    Used for:
    - Top movies bar chart
    - Recent bookings table
    
    Returns:
        JSON: {
            "movies": [
                {"title": "Movie Name", "bookings": 76},
                ...
            ],
            "bookings": [
                {
                    "user": "username",
                    "movie": "Movie Title",
                    "amount": 500.0,
                    "date": "2026-01-09 15:59"
                },
                ...
            ]
        }
    """
    # Get top 5 movies by booking count
    movies = Movie.objects.annotate(
        booking_count=Count('showtime__booking', filter=Q(showtime__booking__status='CONFIRMED'))
    ).filter(booking_count__gt=0).order_by('-booking_count')[:5]
    
    movie_data = [
        {
            'title': m.title,
            'bookings': m.booking_count,
        }
        for m in movies
    ]
    
    # Get 5 most recent confirmed bookings
    recent = Booking.objects.filter(
        status='CONFIRMED'
    ).select_related('user', 'showtime__movie').order_by('-created_at')[:5]
    
    booking_data = [
        {
            'user': b.user.username,
            'movie': b.showtime.movie.title,
            'amount': float(b.total_amount),
            'date': b.created_at.strftime('%Y-%m-%d %H:%M'),
        }
        for b in recent
    ]
    
    return JsonResponse({
        'movies': movie_data,
        'bookings': booking_data,
    })


@staff_member_required(login_url='custom_admin:login')
@require_http_methods(["GET"])
def api_theaters(request):
    """
    Get theater performance data.
    
    Retrieves top 5 theaters by revenue from confirmed bookings.
    Includes booking count and total revenue for each theater.
    
    Used for:
    - Top theaters bar chart
    
    Returns:
        JSON: {
            "theaters": [
                {
                    "name": "Theater Name",
                    "bookings": 33,
                    "revenue": 25287.4
                },
                ...
            ]
        }
    """
    # Annotate theaters with booking count and revenue
    theaters = Theater.objects.annotate(
        booking_count=Count('screen__showtime__booking', filter=Q(screen__showtime__booking__status='CONFIRMED')),
        revenue=Sum('screen__showtime__booking__total_amount', filter=Q(screen__showtime__booking__status='CONFIRMED'))
    ).filter(booking_count__gt=0).order_by('-revenue')[:5]
    
    # Build response data
    theater_data = [
        {
            'name': t.name,
            'bookings': t.booking_count or 0,
            'revenue': float(t.revenue or 0),
        }
        for t in theaters
    ]
    
    return JsonResponse({
        'theaters': theater_data,
    })


@staff_member_required(login_url='custom_admin:login')
def movie_management(request):
    """
    Movie management page for adding and managing movies.
    
    Displays a complete visual guide for:
    - Adding new movies with details (title, duration, genres, etc.)
    - Scheduling showtimes across theaters
    - Managing existing movies and showtimes
    - Viewing and editing movie information
    
    Access: Only staff members
    
    Returns:
        HTML page with movie management interface
    """
    return render(request, 'custom_admin/movie_management.html')
