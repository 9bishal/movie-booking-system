import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from movies.models import Genre, Language, Movie
from movies.theater_models import City, Theater, Screen, Showtime

def create_sample_data():
    print("Creating sample data...")
    
    # Clear existing data
    Genre.objects.all().delete()
    Language.objects.all().delete()
    Movie.objects.all().delete()
    City.objects.all().delete()
    
    # Create Genres
    genres_data = [
        {'name': 'Action', 'icon': 'fas fa-explosion'},
        {'name': 'Comedy', 'icon': 'fas fa-laugh'},
        {'name': 'Drama', 'icon': 'fas fa-theater-masks'},
        {'name': 'Horror', 'icon': 'fas fa-ghost'},
        {'name': 'Romance', 'icon': 'fas fa-heart'},
        {'name': 'Sci-Fi', 'icon': 'fas fa-robot'},
        {'name': 'Thriller', 'icon': 'fas fa-user-secret'},
        {'name': 'Animation', 'icon': 'fas fa-film'},
    ]
    
    for genre_data in genres_data:
        Genre.objects.create(**genre_data)
    
    print("✓ Created genres")
    
    # Create Languages
    languages_data = [
        {'name': 'Hindi', 'code': 'hi'},
        {'name': 'English', 'code': 'en'},
        {'name': 'Tamil', 'code': 'ta'},
        {'name': 'Telugu', 'code': 'te'},
        {'name': 'Kannada', 'code': 'kn'},
    ]
    
    for lang_data in languages_data:
        Language.objects.create(**lang_data)
    
    print("✓ Created languages")
    
    # Create Movies
    movies_data = [
        {
            'title': 'The Last Adventure',
            'description': 'An epic journey through uncharted territories with breathtaking visuals.',
            'duration': 145,
            'release_date': date(2024, 3, 15),
            'certificate': 'UA',
            'rating': 8.5,
            'director': 'Christopher Nolan',
            'cast': 'Tom Hardy, Anne Hathaway, Michael Caine',
        },
        {
            'title': 'Love in Paris',
            'description': 'A romantic comedy set in the beautiful city of Paris.',
            'duration': 120,
            'release_date': date(2024, 2, 14),
            'certificate': 'U',
            'rating': 7.2,
            'director': 'Emma Stone',
            'cast': 'Ryan Gosling, Emma Watson',
        },
        {
            'title': 'Space Odyssey 2024',
            'description': 'Interstellar travel and alien encounters in this sci-fi thriller.',
            'duration': 165,
            'release_date': date(2024, 1, 10),
            'certificate': 'UA',
            'rating': 8.9,
            'director': 'James Cameron',
            'cast': 'Matt Damon, Jessica Chastain',
        },
        {
            'title': 'The Mystery of Hill House',
            'description': 'A family moves into a haunted house with dark secrets.',
            'duration': 110,
            'release_date': date(2024, 3, 1),
            'certificate': 'A',
            'rating': 7.8,
            'director': 'Mike Flanagan',
            'cast': 'Victoria Pedretti, Oliver Jackson-Cohen',
        },
    ]
    
    hindi_lang = Language.objects.get(code='hi')
    english_lang = Language.objects.get(code='en')
    
    for i, movie_data in enumerate(movies_data):
        movie = Movie.objects.create(
            **movie_data,
            language=hindi_lang if i % 2 == 0 else english_lang,
            trailer_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        )
        
        # Add genres
        if i == 0:  # Action/Sci-Fi
            movie.genres.add(Genre.objects.get(name='Action'))
            movie.genres.add(Genre.objects.get(name='Sci-Fi'))
        elif i == 1:  # Romance/Comedy
            movie.genres.add(Genre.objects.get(name='Romance'))
            movie.genres.add(Genre.objects.get(name='Comedy'))
        elif i == 2:  # Sci-Fi/Thriller
            movie.genres.add(Genre.objects.get(name='Sci-Fi'))
            movie.genres.add(Genre.objects.get(name='Thriller'))
        else:  # Horror/Thriller
            movie.genres.add(Genre.objects.get(name='Horror'))
            movie.genres.add(Genre.objects.get(name='Thriller'))
    
    print("✓ Created movies")
    
    # Create Cities
    cities_data = [
        {'name': 'Mumbai'},
        {'name': 'Delhi'},
        {'name': 'Bangalore'},
        {'name': 'Chennai'},
        {'name': 'Hyderabad'},
    ]
    
    for city_data in cities_data:
        City.objects.create(**city_data)
    
    print("✓ Created cities")
    
    # Create Theaters
    mumbai = City.objects.get(name='Mumbai')
    delhi = City.objects.get(name='Delhi')
    
    theaters_data = [
        {'name': 'PVR Cinemas', 'city': mumbai, 'address': 'Phoenix Marketcity, Kurla'},
        {'name': 'INOX Megaplex', 'city': mumbai, 'address': 'R-City Mall, Ghatkopar'},
        {'name': 'Cinepolis', 'city': delhi, 'address': 'Select Citywalk, Saket'},
        {'name': 'IMAX Delhi', 'city': delhi, 'address': 'DLF Promenade, Vasant Kunj'},
    ]
    
    for theater_data in theaters_data:
        Theater.objects.create(**theater_data)
    
    print("✓ Created theaters")
    
    # Create Screens
    pvr = Theater.objects.get(name='PVR Cinemas')
    inox = Theater.objects.get(name='INOX Megaplex')
    cinepolis = Theater.objects.get(name='Cinepolis')
    imax = Theater.objects.get(name='IMAX Delhi')
    
    screens_data = [
        {'theater': pvr, 'name': 'Screen 1', 'screen_type': '2D', 'total_seats': 150},
        {'theater': pvr, 'name': 'Screen 2', 'screen_type': '3D', 'total_seats': 120},
        {'theater': inox, 'name': 'Screen A', 'screen_type': '2D', 'total_seats': 200},
        {'theater': inox, 'name': 'Screen B', 'screen_type': 'IMAX', 'total_seats': 250},
        {'theater': cinepolis, 'name': 'Screen 1', 'screen_type': '2D', 'total_seats': 180},
        {'theater': imax, 'name': 'IMAX Hall', 'screen_type': 'IMAX', 'total_seats': 300},
    ]
    
    for screen_data in screens_data:
        Screen.objects.create(**screen_data)
    
    print("✓ Created screens")
    
    # Create Showtimes
    adventure_movie = Movie.objects.get(title='The Last Adventure')
    love_movie = Movie.objects.get(title='Love in Paris')
    
    # Create showtimes for next 7 days
    for i in range(7):
        show_date = date.today() + timedelta(days=i)
        
        # Morning shows
        Showtime.objects.create(
            movie=adventure_movie,
            screen=Screen.objects.get(theater=pvr, name='Screen 1'),
            date=show_date,
            start_time='10:00',
            end_time='12:25',
            price=250.00,
            available_seats=150
        )
        
        # Afternoon shows
        Showtime.objects.create(
            movie=love_movie,
            screen=Screen.objects.get(theater=inox, name='Screen A'),
            date=show_date,
            start_time='13:30',
            end_time='15:30',
            price=200.00,
            available_seats=200
        )
        
        # Evening shows
        Showtime.objects.create(
            movie=adventure_movie,
            screen=Screen.objects.get(theater=imax, name='IMAX Hall'),
            date=show_date,
            start_time='18:00',
            end_time='20:45',
            price=350.00,
            available_seats=300
        )
    
    print("✓ Created showtimes")
    print("\n✅ Sample data created successfully!")
    print("\nYou can now:")
    print("1. Visit http://127.0.0.1:8000/ to see the home page")
    print("2. Visit http://127.0.0.1:8000/admin/ to manage data")
    print("3. Visit http://127.0.0.1:8000/movies/ to browse movies")

if __name__ == '__main__':
    create_sample_data()