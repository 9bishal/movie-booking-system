from django.test import TestCase
from movies.models import Movie, Genre, Language
from datetime import date

class MovieModelTest(TestCase):
    def setUp(self):
        self.language = Language.objects.create(name="English", code="en")
        self.genre = Genre.objects.create(name="Action", slug="action")
        self.movie = Movie.objects.create(
            title="Test Movie",
            description="A test movie description",
            duration=120,
            release_date=date.today(),
            language=self.language
        )
        self.movie.genres.add(self.genre)

    def test_movie_creation(self):
        self.assertEqual(self.movie.title, "Test Movie")
        self.assertEqual(self.movie.slug, "test-movie")
        self.assertEqual(self.movie.duration_formatted(), "2h 0m")
