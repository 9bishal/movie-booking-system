import time
from django.core.cache import cache
from django.db import connection
import psutil
import os
from django.conf import settings


class PerformanceMonitor:
    """Monitor application performance"""
    
    @staticmethod
    def get_system_stats():
        """Get system statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'process_memory': psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024,  # MB
        }
    
    @staticmethod
    def get_database_stats():
        """Get database statistics"""
        with connection.cursor() as cursor:
            # Get query count
            cursor.execute("SELECT count(*) FROM information_schema.processlist")
            connections = cursor.fetchone()[0]
            
            # Get table sizes (MySQL/PostgreSQL specific)
            # Simplified for SQLite
            return {
                'connections': connections,
                'queries_executed': len(connection.queries) if hasattr(connection, 'queries') else 0,
            }
    
    @staticmethod
    def get_cache_stats():
        """Get cache statistics"""
        try:
            # Test cache
            test_key = 'performance_test'
            cache.set(test_key, 'test', 1)
            hit = cache.get(test_key) is not None
            cache.delete(test_key)
            
            return {
                'cache_hit': hit,
                'cache_backend': settings.CACHES['default']['BACKEND'],
            }
        except:
            return {'cache_hit': False, 'error': 'Cache unavailable'}
    
    @staticmethod
    def measure_performance(view_func):
        """Decorator to measure view performance"""
        from functools import wraps
        import logging
        
        logger = logging.getLogger('performance')
        
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            start_queries = len(connection.queries) if hasattr(connection, 'queries') else 0
            
            response = view_func(request, *args, **kwargs)
            
            end_time = time.time()
            end_queries = len(connection.queries) if hasattr(connection, 'queries') else 0
            
            # Log performance
            performance_data = {
                'view': view_func.__name__,
                'url': request.path,
                'response_time': round((end_time - start_time) * 1000, 2),  # ms
                'queries': end_queries - start_queries,
                'method': request.method,
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
            }
            
            logger.info(f"Performance: {performance_data}")
            
            # Add header for debugging
            if settings.DEBUG:
                response['X-Performance-Time'] = f"{performance_data['response_time']}ms"
                response['X-Performance-Queries'] = performance_data['queries']
            
            return response
        return wrapper