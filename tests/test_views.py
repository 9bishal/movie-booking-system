from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from movies.models import Movie, Language

class HomeViewTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.language = Language.objects.create(name='English', code='en')
        
        # Create test movies
        Movie.objects.create(
            title='Movie 1',
            description='Description 1',
            duration=120,
            release_date='2024-01-01',
            language=self.language,
            is_active=True
        )
        Movie.objects.create(
            title='Movie 2',
            description='Description 2',
            duration=150,
            release_date='2024-02-01',
            language=self.language,
            is_active=True
        )
    
    def test_home_view_status(self):
        """Test home page loads successfully"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_home_view_context(self):
        """Test home page context"""
        response = self.client.get(reverse('home'))
        self.assertIn('featured_movies', response.context)
        self.assertIn('now_showing', response.context)
    
    def test_home_view_template(self):
        """Test home page uses correct template"""
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'movies/home.html')

class AuthenticationTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_login_view_get(self):
        """Test login page loads"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
    
    def test_login_success(self):
        """Test successful login"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
    
    def test_login_failure(self):
        """Test failed login"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
    
    def test_registration(self):
        """Test user registration"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after registration
        self.assertTrue(User.objects.filter(username='newuser').exists())