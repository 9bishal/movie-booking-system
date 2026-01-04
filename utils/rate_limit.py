# Django's cache system
# Used to temporarily store data (very fast, auto-expiring)
from django.core.cache import cache

# Used to send JSON responses (mainly for API / AJAX calls)
from django.http import JsonResponse

# Used to get the current time (timestamps)
import time


class RateLimiter:
    """
    Custom Rate Limiter class

    Purpose:
    --------
    To limit how many requests a user or IP address
    can make within a specific time window.

    Example:
    --------
    - Login: max 5 requests per minute
    - API: max 60 requests per minute
    """

    def __init__(self, rate='5/m', key_prefix='rl'):
        """
        Constructor (runs when RateLimiter object is created)

        Parameters:
        -----------
        rate (str):
            Rate limit format → 'number/period'
            Examples:
            - '5/m'  → 5 requests per minute
            - '10/s' → 10 requests per second
            - '100/h' → 100 requests per hour

        key_prefix (str):
            Prefix added to cache keys
            Helps avoid clashes between different limiters

        Example cache keys:
        -------------------
        login_user_42
        booking_ip_192.168.1.1
        """
 
        self.rate = rate
        self.key_prefix = key_prefix


    def parse_rate(self, rate):
        """
        Converts a rate string into usable numbers

        Example:
        --------
        '5/m' → (5, 60)

        Meaning:
        --------
        Allow 5 requests in 60 seconds
        """

        # Split the rate string (e.g., '5/m')
        num, period = rate.split('/')

        # Convert '5' → 5 (integer)
        num = int(num)

        # Convert time period into seconds
        if period == 's':
            period_seconds = 1
        elif period == 'm':
            period_seconds = 60
        elif period == 'h':
            period_seconds = 3600  # 60 × 60
        elif period == 'd':
            period_seconds = 86400  # 24 × 60 × 60
        else:
            # Invalid format protection
            raise ValueError(f"Invalid period: {period}")

        return num, period_seconds


    def is_allowed(self, request, identifier=None):
        """
        Core logic: decides whether the request is allowed or blocked

        Returns:
        --------
        (True, num, period)  → Request allowed
        (False, num, period) → Rate limit exceeded
        """

        # If identifier not provided, automatically determine it
        # (user ID if logged in, otherwise IP address)
        if identifier is None:
            identifier = self.get_identifier(request)

        # Convert rate like '5/m' → (5, 60)
        num, period = self.parse_rate(self.rate)

        # Build a unique cache key
        # Example:
        #   login_user_42
        #   api_ip_192.168.1.10
        cache_key = f"{self.key_prefix}_{identifier}"

        # Get existing request timestamps from cache
        # If nothing exists yet, return empty list
        requests = cache.get(cache_key, [])

        # Current timestamp (seconds since epoch)
        now = time.time()

        # Remove old requests outside the allowed time window
        # Example: keep only last 60 seconds
        cutoff_time = now - period
        requests = [
            req_time for req_time in requests
            if req_time > cutoff_time
        ]

        # If request count exceeds allowed limit → BLOCK
        if len(requests) >= num:
            return False, num, period

        # Otherwise, allow the request
        # Add current request timestamp
        requests.append(now)

        # Save updated timestamps back to cache
        # Cache auto-expires after "period" seconds
        cache.set(cache_key, requests, period)

        return True, num, period


    def get_identifier(self, request):
        """
        Identifies WHO is making the request

        Priority:
        ---------
        1️⃣ Logged-in user → user ID
        2️⃣ Anonymous user → IP address
        """

        if request.user.is_authenticated:
            # Example: user_42
            return f"user_{request.user.id}"
        else:
            # Example: ip_192.168.1.1
            return f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"


    def rate_limit_view(self, view_func):
        """
        Decorator that applies rate limiting to a Django view

        Usage:
        ------
        @login_limiter.rate_limit_view
        def login_view(request):
            ...
        """

        from functools import wraps

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # Check if request is allowed
            allowed, num, period = self.is_allowed(request)

            # If NOT allowed → return error response
            if not allowed:

                # If it's an API / AJAX request → JSON response
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(
                        {
                            'error': 'Rate limit exceeded',
                            'message': f'Too many requests. Limit is {num} per {period} seconds.'
                        },
                        status=429  # HTTP 429 = Too Many Requests
                    )

                # Otherwise → normal HTML error page
                from django.shortcuts import render
                return render(
                    request,
                    'errors/429.html',
                    {
                        'limit': num,
                        'period': period
                    },
                    status=429
                )

            # If allowed → proceed to actual view
            return view_func(request, *args, **kwargs)

        return wrapper


# ================================
# READY-TO-USE RATE LIMITERS
# ================================

# Login protection:
# Max 5 attempts per minute
login_limiter = RateLimiter(rate='5/m', key_prefix='login')

# Booking protection (general):
# Max 30 actions per minute (increased for better UX)
booking_limiter = RateLimiter(rate='30/m', key_prefix='booking')

# Seat selection protection (more lenient):
# Max 50 requests per minute (users frequently change seat selection)
seat_selection_limiter = RateLimiter(rate='50/m', key_prefix='seat_select')

# Payment protection (stricter):
# Max 5 payment attempts per minute (prevent abuse)
payment_limiter = RateLimiter(rate='5/m', key_prefix='payment')

# API protection:
# Max 60 requests per minute
api_limiter = RateLimiter(rate='60/m', key_prefix='api')
