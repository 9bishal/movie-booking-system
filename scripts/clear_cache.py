#!/usr/bin/env python
"""
Clear all cache (Redis/Django cache)
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.core.cache import cache

def clear_cache():
    print("🧹 Clearing all cache...")
    cache.clear()
    print("✅ Cache cleared successfully!")

if __name__ == '__main__':
    clear_cache()
