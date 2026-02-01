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
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
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
    
    Supports filtering by date range, movie, and theater.
    Only shows CONFIRMED bookings.
    
    Query Parameters:
        date_from (str): Start date (YYYY-MM-DD)
        date_to (str): End date (YYYY-MM-DD)
        movie_id (int): Movie ID filter
        theater_id (int): Theater ID filter
    
    Calculates:
    - Total revenue from bookings (all time or filtered)
    - Today's revenue from bookings
    - Total booking count (all time or filtered)
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
    
    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    movie_id = request.GET.get('movie_id', '')
    theater_id = request.GET.get('theater_id', '')
    
    # Build base query - only confirmed bookings
    base_query = Booking.objects.filter(status='CONFIRMED')
    
    # Apply date range filter
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            base_query = base_query.filter(created_at__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            base_query = base_query.filter(created_at__date__lte=to_date)
        except ValueError:
            pass
    
    # Apply movie filter
    if movie_id:
        try:
            base_query = base_query.filter(showtime__movie_id=int(movie_id))
        except (ValueError, TypeError):
            pass
    
    # Apply theater filter
    if theater_id:
        try:
            base_query = base_query.filter(showtime__screen__theater_id=int(theater_id))
        except (ValueError, TypeError):
            pass
    
    # Calculate total revenue from filtered bookings
    total_revenue = base_query.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Calculate today's revenue
    today_revenue = base_query.filter(
        created_at__date=today
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Count total bookings
    total_bookings = base_query.count()
    
    # Count today's bookings
    today_bookings = base_query.filter(
        created_at__date=today
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
    Get daily revenue data for the last N days or custom date range.
    
    Supports filtering by date range, movie, and theater.
    Only shows CONFIRMED bookings.
    
    Query Parameters:
        days (int): Number of days to fetch (default: 30)
        date_from (str): Start date (YYYY-MM-DD)
        date_to (str): End date (YYYY-MM-DD)
        movie_id (int): Movie ID filter
        theater_id (int): Theater ID filter
    
    Used to render the revenue trend line chart on dashboard.
    Returns daily revenue totals for each date in the range.
    
    Returns:
        JSON: {
            "dates": ["2025-12-10", "2025-12-11", ...],
            "revenues": [0.0, 2500.0, ...]
        }
    """
    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    movie_id = request.GET.get('movie_id', '')
    theater_id = request.GET.get('theater_id', '')
    
    # Calculate date range
    if date_from and date_to:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            start_date = timezone.now().date() - timedelta(days=30)
            end_date = timezone.now().date()
    else:
        # Default to last 30 days
        days = int(request.GET.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
    
    dates = []
    revenues = []
    
    # Iterate through each day and calculate revenue
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        
        # Build query with filters - only confirmed bookings
        query = Booking.objects.filter(
            created_at__date=current_date,
            status='CONFIRMED'
        )
        
        # Apply movie filter
        if movie_id:
            try:
                query = query.filter(showtime__movie_id=int(movie_id))
            except (ValueError, TypeError):
                pass
        
        # Apply theater filter
        if theater_id:
            try:
                query = query.filter(showtime__screen__theater_id=int(theater_id))
            except (ValueError, TypeError):
                pass
        
        # Sum revenue for this day
        daily_revenue = query.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
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
    Get top movies and recent bookings data with optional filtering.
    
    Supports filtering by date range, movie, and theater.
    Only shows CONFIRMED bookings.
    
    Query Parameters:
        date_from (str): Start date (YYYY-MM-DD)
        date_to (str): End date (YYYY-MM-DD)
        movie_id (int): Movie ID filter
        theater_id (int): Theater ID filter
    
    Calculates:
    1. Top 5 movies by number of bookings (with filters)
    2. 5 most recent bookings with user and movie details (with filters)
    
    Used for:
    - Top movies bar chart
    - Recent bookings table
    
    Returns:
        JSON: {
            "movies": [
                {"id": 1, "title": "Movie Name", "bookings": 76},
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
    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    movie_id = request.GET.get('movie_id', '')
    theater_id = request.GET.get('theater_id', '')
    
    # Build base query - only confirmed bookings
    base_query = Booking.objects.filter(status='CONFIRMED')
    
    # Apply date range filter
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            base_query = base_query.filter(created_at__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            base_query = base_query.filter(created_at__date__lte=to_date)
        except ValueError:
            pass
    
    # Apply movie filter
    if movie_id:
        try:
            base_query = base_query.filter(showtime__movie_id=int(movie_id))
        except (ValueError, TypeError):
            pass
    
    # Apply theater filter
    if theater_id:
        try:
            base_query = base_query.filter(showtime__screen__theater_id=int(theater_id))
        except (ValueError, TypeError):
            pass
    
    # Get list of movie IDs from filtered bookings
    movie_ids = base_query.values_list('showtime__movie_id', flat=True).distinct()
    
    # Get top 5 movies by booking count (with filters)
    movies = Movie.objects.filter(id__in=movie_ids).annotate(
        booking_count=Count('showtime__booking', filter=Q(showtime__booking__in=base_query))
    ).order_by('-booking_count')[:5]
    
    movie_data = [
        {
            'id': m.id,
            'title': m.title,
            'bookings': m.booking_count,
        }
        for m in movies
    ]
    
    # Get 5 most recent bookings (with filters)
    recent = base_query.select_related('user', 'showtime__movie').order_by('-created_at')[:5]
    
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
    Get theater performance data with optional filtering.
    
    Retrieves top 5 theaters by revenue from confirmed bookings.
    Includes booking count, revenue, and ID for each theater.
    Supports filtering by date range, movie, and theater.
    
    Query Parameters:
        date_from (str): Start date (YYYY-MM-DD)
        date_to (str): End date (YYYY-MM-DD)
        movie_id (int): Movie ID filter
        theater_id (int): Theater ID filter
    
    Used for:
    - Top theaters bar chart
    
    Returns:
        JSON: {
            "theaters": [
                {
                    "id": 1,
                    "name": "Theater Name",
                    "bookings": 33,
                    "revenue": 25287.4
                },
                ...
            ]
        }
    """
    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    movie_id = request.GET.get('movie_id', '')
    theater_id = request.GET.get('theater_id', '')
    
    # Build base booking query with filters - only confirmed bookings
    base_query = Booking.objects.filter(status='CONFIRMED')
    
    # Apply date range filter
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            base_query = base_query.filter(created_at__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            base_query = base_query.filter(created_at__date__lte=to_date)
        except ValueError:
            pass
    
    # Apply movie filter
    if movie_id:
        try:
            base_query = base_query.filter(showtime__movie_id=int(movie_id))
        except (ValueError, TypeError):
            pass
    
    # Apply theater filter
    if theater_id:
        try:
            base_query = base_query.filter(showtime__screen__theater_id=int(theater_id))
        except (ValueError, TypeError):
            pass
    
    # Get list of theater IDs from filtered bookings
    theater_ids = base_query.values_list('showtime__screen__theater_id', flat=True).distinct()
    
    # Annotate theaters with booking count and revenue based on filtered bookings
    theaters = Theater.objects.filter(id__in=theater_ids).annotate(
        booking_count=Count('screen__showtime__booking', filter=Q(screen__showtime__booking__in=base_query)),
        revenue=Sum('screen__showtime__booking__total_amount', filter=Q(screen__showtime__booking__in=base_query))
    ).order_by('-revenue')[:5]
    
    # Build response data
    theater_data = [
        {
            'id': t.id,
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
@require_http_methods(["GET"])
def api_movies_list(request):
    """
    Get list of all movies for filter dropdown.
    
    Returns:
        JSON: {
            "movies": [
                {"id": 1, "title": "Movie Name"},
                ...
            ]
        }
    """
    movies = Movie.objects.all().values('id', 'title').order_by('title')
    
    return JsonResponse({
        'movies': list(movies),
    })


@staff_member_required(login_url='custom_admin:login')
@require_http_methods(["GET"])
def api_theaters_list(request):
    """
    Get list of all theaters for filter dropdown.
    
    Returns:
        JSON: {
            "theaters": [
                {"id": 1, "name": "Theater Name"},
                ...
            ]
        }
    """
    theaters = Theater.objects.all().values('id', 'name').order_by('name')
    
    return JsonResponse({
        'theaters': list(theaters),
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
