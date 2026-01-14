#!/usr/bin/env python
"""
Create sample data for testing
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from movies.models import Movie
from movies.theater_models import Theater, Screen, Showtime

def create_sample_data():
    print("🎬 Creating sample data...")
    
    # Create movie
    movie, created = Movie.objects.get_or_create(
        title="Sample Movie",
        defaults={
            'description': 'A sample movie for testing',
            'duration_minutes': 120,
            'release_date': timezone.now().date(),
            'is_active': True,
        }
    )
    print(f"{'✅ Created' if created else '📌 Found'} movie: {movie.title}")
    
    # Create theater
    theater, created = Theater.objects.get_or_create(
        name="Sample Theater",
        defaults={
            'address': '123 Main Street',
            'city': 'Sample City',
        }
    )
    print(f"{'✅ Created' if created else '📌 Found'} theater: {theater.name}")
    
    # Create screen
    screen, created = Screen.objects.get_or_create(
        theater=theater,
        name="Screen 1",
        defaults={
            'screen_type': '2D',
            'total_seats': 100,
        }
    )
    print(f"{'✅ Created' if created else '📌 Found'} screen: {screen.name}")
    
    # Create showtime
    showtime, created = Showtime.objects.get_or_create(
        movie=movie,
        screen=screen,
        date=timezone.now().date() + timedelta(days=1),
        time=timezone.now().time().replace(hour=18, minute=0),
        defaults={
            'price': Decimal('200.00'),
            'is_active': True,
        }
    )
    print(f"{'✅ Created' if created else '📌 Found'} showtime: {showtime}")
    
    print("\n✅ Sample data ready!")
    print(f"🔗 Visit: /bookings/select-seats/{showtime.id}/")

if __name__ == '__main__':
    create_sample_data()
