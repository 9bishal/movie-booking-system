from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json

def cache_page(timeout=300, key_prefix=''):
    """
    Decorator for caching view responses.
    
    This decorator caches the entire HTTP response of Django views to 
    improve performance by reducing database queries and view processing.
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Optional prefix for cache keys to avoid collisions
    
    Usage:
        @cache_page(timeout=600)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)  # Preserves original function metadata
        def _wrapped_view(request, *args, **kwargs):
            # Generate cache key from request - unique identifier for cached response
            cache_key = f"{key_prefix}_{request.path}"
            
            # Include query parameters in cache key
            # Different query params should have different cache entries
            if request.GET:
                # Hash the sorted query parameters to ensure consistent keys
                query_hash = hashlib.md5(
                    json.dumps(dict(request.GET), sort_keys=True).encode()
                ).hexdigest()
                cache_key += f"_{query_hash}"
            
            # Include user-specific cache for authenticated users
            # This ensures different users get different cached responses
            # Important for personalized content or permissions
            if request.user.is_authenticated:
                cache_key += f"_user_{request.user.id}"
            
            # Try to get from cache - cache.get() returns None if not found
            response = cache.get(cache_key)
            
            if response is None:
                # Cache miss - call the original view function
                response = view_func(request, *args, **kwargs)
                
                # Cache the response
                # Check if response is a TemplateResponse (needs rendering)
                if hasattr(response, 'render'):
                    # For TemplateResponse, cache after it's fully rendered
                    response.add_post_render_callback(
                        lambda r: cache.set(cache_key, r, timeout)
                    )
                else:
                    # For regular HttpResponse, cache immediately
                    cache.set(cache_key, response, timeout)
            
            return response  # Return cached or fresh response
        return _wrapped_view
    return decorator

def cache_model(model_name, timeout=3600):
    """
    Cache model queryset results or function results.
    
    This decorator caches the results of functions that return database querysets
    or other expensive-to-compute data related to models.
    
    Args:
        model_name: Name of the model (used in cache key)
        timeout: Cache timeout in seconds (default: 1 hour)
    
    Usage:
        @cache_model('movie', timeout=600)
        def get_popular_movies():
            return Movie.objects.filter(rating__gte=8.0)
    """
    def decorator(func):
        @wraps(func)  # Preserves function name and docstring
        def wrapper(*args, **kwargs):
            # Generate cache key based on function name and arguments
            # This ensures different arguments get different cache entries
            key = f"{model_name}_{func.__name__}"
            
            # Include function arguments in cache key
            # Hash arguments to avoid overly long cache keys
            if args:
                key += f"_{hashlib.md5(str(args).encode()).hexdigest()[:8]}"  # First 8 chars of hash
            if kwargs:
                key += f"_{hashlib.md5(str(kwargs).encode()).hexdigest()[:8]}"
            
            # Try to get result from cache
            result = cache.get(key)
            if result is not None:
                return result  # Return cached result if found
            
            # Cache miss - execute the original function
            result = func(*args, **kwargs)
            
            # Store result in cache for future requests
            cache.set(key, result, timeout)
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern):
    """
    Invalidate cache keys matching a pattern.
    
    This function is used to clear cache entries when data changes,
    ensuring users see fresh data after updates.
    
    Args:
        pattern: String pattern to match against cache keys
    
    Usage:
        invalidate_cache('movie_')  # Clears all cache keys starting with 'movie_'
    
    Important: Uses Redis SCAN instead of KEYS for better performance with large datasets
    """
    from django_redis import get_redis_connection
    
    # Get Redis connection using Django's cache configuration
    redis = get_redis_connection("default")
    
    # Use SCAN for large datasets (safer than KEYS command)
    # KEYS command can block Redis on large databases, SCAN is non-blocking
    cursor = '0'
    while cursor != 0:
        # SCAN returns a cursor and matching keys
        cursor, keys = redis.scan(cursor, match=f'*{pattern}*', count=100)
        if keys:
            # Delete all matching keys
            redis.delete(*keys)

class CacheManager:
    """
    Manage application cache with specific use cases.
    
    This class provides organized methods for caching common operations,
    making cache management consistent across the application.
    """
    
    @staticmethod
    def cache_movie_list(timeout=600):
        """
        Cache movie listings with related data.
        
        This optimizes the movie listing page by caching:
        - Movie data
        - Related language data
        - Related genres data
        
        Returns a function that when called, returns cached or fresh movie list
        """
        @cache_model('movie_list', timeout)  # Decorator caches the function results
        def get_movies():
            from movies.models import Movie
            # Fetch movies with optimized queries to avoid N+1 problems
            return list(Movie.objects.filter(is_active=True)
                       .select_related('language')  # Single query for language
                       .prefetch_related('genres')   # Optimized query for genres
                       .only('title', 'slug', 'rating', 'release_date', 
                             'duration', 'poster', 'language__name'))  # Select only needed fields
        return get_movies  # Return the decorated function
    
    @staticmethod
    def cache_showtimes(movie_id, timeout=300):
        """
        Cache showtimes for a specific movie.
        
        This is useful for movie detail pages where showtimes are displayed.
        Shorter timeout (5 minutes) as showtimes change frequently.
        """
        @cache_model(f'showtimes_{movie_id}', timeout)
        def get_showtimes():
            from movies.models import Showtime
            from django.utils import timezone
            # Fetch only future showtimes for active screens
            return list(Showtime.objects.filter(
                movie_id=movie_id,
                is_active=True,
                date__gte=timezone.now().date()  # Only future dates
            ).select_related('screen__theater')  # Get theater info
             .order_by('date', 'start_time'))  # Consistent ordering
        return get_showtimes
    
    @staticmethod
    def clear_movie_cache(movie_id=None):
        """
        Clear movie-related cache when data changes.
        
        Should be called when:
        1. A movie is added/updated/deleted
        2. Showtimes change
        3. Any related data changes
        
        Args:
            movie_id: Optional specific movie ID to clear only its showtimes cache
        """
        if movie_id:
            # Clear showtimes cache for specific movie
            invalidate_cache(f'showtimes_{movie_id}')
        # Always clear movie list cache as any movie change affects the list
        invalidate_cache('movie_list')