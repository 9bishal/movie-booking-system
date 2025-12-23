from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Movie, Genre, Language
from .theater_models import City, Showtime
from django.db.models import Q

# ==============================================================================
# ❓ WHAT ARE VIEWS?
# Views are the "Logic" layer of Django (The 'C' in MVC).
# They receive a web request, fetch data from the Database (Models),
# and return a response (usually an HTML Template).
# ==============================================================================

# ========== MOVIE LIST VIEW ==========
def movie_list(request):
    """Display all active movies"""
    # ❓ WHY filter(is_active=True)?
    # We only want to show movies that are currently manageable/released.
    # Deleted or draft movies should be hidden.
    movies = Movie.objects.filter(is_active=True).order_by('-release_date')
    
    # Get filters from request (e.g., /movies/?genre=action)
    genre_filter = request.GET.get('genre', '')
    language_filter = request.GET.get('language', '')
    search_query = request.GET.get('search', '')
    
    # Apply filters
    if genre_filter:
        # Django 'Double Underscore' syntax (__) allows us to query related fields.
        # Here we check if the genres' slug matches the filter.
        movies = movies.filter(genres__slug=genre_filter)
    
    if language_filter:
        movies = movies.filter(language__code=language_filter)
    
    # ❓ WHY USE Q Objects?
    # Standard filter() arguments are "AND"ed together (e.g. title="X" AND year=2024).
    # 'Q' objects allow us to use "OR" logic (|).
    # Here we search if the query is in the Title OR Description OR Director OR Cast.
    if search_query:
        movies = movies.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(director__icontains=search_query) |
            Q(cast__icontains=search_query)
        )
    
    # Get all genres and languages for filter sidebar
    genres = Genre.objects.all()
    languages = Language.objects.all()
    
    # ❓ WHAT IS CONTEXT?
    # Context is a dictionary that passes data from this Python file
    # to the HTML template. The keys ('movies') are what you access in HTML tags ({{ movies }}).
    context = {
        'movies': movies,
        'genres': genres,
        'languages': languages,
        'selected_genre': genre_filter,
        'selected_language': language_filter,
        'search_query': search_query,
    }
    
    # render() combines the request, the template, and the data (context)
    # to produce the final HTML page sent to the user.
    return render(request, 'movies/movie_list.html', context)

# ========== MOVIE DETAIL VIEW ==========
def movie_detail(request, slug):
    """Display movie details and available showtimes"""
    # ❓ WHY get_object_or_404?
    # If a user types a wrong URL (/movies/non-existent-movie/),
    # Movie.objects.get() would crash with a "DoesNotExist" error (500 Server Error).
    # get_object_or_404 catches this and safely shows a "404 Not Found" page.
    movie = get_object_or_404(Movie, slug=slug, is_active=True)
    
    # Get showtimes for this movie
    showtimes = Showtime.objects.filter(
        movie=movie,
        is_active=True
    ).order_by('date', 'start_time')
    
    # Group showtimes by city for easier display in the UI
    cities_with_showtimes = []
    cities = City.objects.filter(is_active=True)
    
    for city in cities:
        # Get theaters in this city with showtimes for this movie
        city_showtimes = showtimes.filter(screen__theater__city=city)
        
        if city_showtimes.exists():
            # Group by theater within the city
            theaters = {}
            for showtime in city_showtimes:
                theater = showtime.screen.theater
                if theater.id not in theaters:
                    theaters[theater.id] = {
                        'theater': theater,
                        'showtimes': []
                    }
                theaters[theater.id]['showtimes'].append(showtime)
            
            cities_with_showtimes.append({
                'city': city,
                'theaters': list(theaters.values())
            })
    
    context = {
        'movie': movie,
        'cities_with_showtimes': cities_with_showtimes,
        'genres': movie.genres.all(),
    }
    
    return render(request, 'movies/movie_detail.html', context)

# ========== HOME PAGE VIEW ==========
def home(request):
    """Home page with featured movies"""
    # Featured movies (most recent 6)
    featured_movies = Movie.objects.filter(is_active=True).order_by('-release_date')[:6]
    
    # Now showing (movies with showtimes in next 7 days)
    from datetime import date, timedelta
    next_week = date.today() + timedelta(days=7)
    
    # Get movies with upcoming showtimes
    # distinct() ensures we don't get duplicate movie IDs if a movie has multiple shows
    upcoming_showtimes = Showtime.objects.filter(
        date__range=[date.today(), next_week],
        is_active=True
    ).values_list('movie_id', flat=True).distinct()
    
    now_showing = Movie.objects.filter(
        id__in=upcoming_showtimes,
        is_active=True
    )[:8]
    
    # Get all genres
    genres = Genre.objects.all()[:10]
    
    context = {
        'featured_movies': featured_movies,
        'now_showing': now_showing,
        'genres': genres,
    }
    
    return render(request, 'movies/home.html', context)