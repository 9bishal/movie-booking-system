#!/usr/bin/env python
"""
Delete all movies and related data
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from movies.models import Movie
from django.core.cache import cache

def delete_all_movies():
    print("🎬 Deleting all movies...")
    
    total = Movie.objects.count()
    print(f"📊 Found {total} movies")
    
    # Delete all movies (cascades to showtimes, etc.)
    deleted, details = Movie.objects.all().delete()
    print(f"✅ Deleted {deleted} items!")
    
    for model, count in details.items():
        if count > 0:
            print(f"   - {model}: {count}")
    
    # Clear cache
    cache.clear()
    print("✅ Cache cleared!")

if __name__ == '__main__':
    confirm = input("⚠️  This will DELETE ALL movies and showtimes. Type 'yes': ")
    if confirm.lower() == 'yes':
        delete_all_movies()
    else:
        print("❌ Cancelled.")
