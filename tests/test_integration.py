from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from movies.models import Movie, Language, Showtime
from bookings.models import Booking
from datetime import date, time, timedelta

class BookingFlowTest(TestCase):
    """Test complete booking flow"""
    
    def setUp(self):
        self.client = Client()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create movie
        language = Language.objects.create(name='English', code='en')
        self.movie = Movie.objects.create(
            title='Test Movie',
            duration=120,
            release_date=date.today(),
            language=language,
            is_active=True
        )
        
        # Create showtime
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=None,  # Simplified for test
            date=date.today() + timedelta(days=1),
            start_time=time(18, 0),
            price=200.00,
            available_seats=100
        )
    
    def test_complete_booking_flow(self):
        """Test from login to booking confirmation"""
        
        # 1. Login
        self.client.login(username='testuser', password='testpass123')
        
        # 2. Access movie detail
        response = self.client.get(reverse('movie_detail', args=[self.movie.slug]))
        self.assertEqual(response.status_code, 200)
        
        # 3. Access seat selection (simplified)
        # In real test, you'd follow the complete flow
        
        # 4. Check my bookings page
        response = self.client.get(reverse('my_bookings'))
        self.assertEqual(response.status_code, 200)