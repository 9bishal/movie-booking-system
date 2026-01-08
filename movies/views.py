from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from .models import Movie, Genre, Language
from .theater_models import City, Showtime
from django.db.models import Q
from .reviews_models import Review, ReviewLike, Wishlist, Interest
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
import json
from embed_video.backends import detect_backend
from django.core.cache import cache

# Import utility functions for performance, caching, and rate limiting
from utils.cache_utils import cache_page, CacheManager
from utils.performance import PerformanceMonitor
from utils.rate_limit import RateLimiter, api_limiter


# ==============================================================================
# ❓ WHAT ARE VIEWS?
# Views are the "Logic" layer of Django (The 'C' in MVC).
# They receive a web request, fetch data from the Database (Models),
# and return a response (usually an HTML Template).
# ==============================================================================

# ========== MOVIE LIST VIEW ==========
# Cache for 12 minutes, monitor performance
@cache_page(timeout=720)
@PerformanceMonitor.measure_performance
def movie_list(request):
    """Display all active movies"""
    # ❓ WHY filter(is_active=True)?
    # We only want to show movies that are currently manageable/released.
    # Deleted or draft movies should be hidden.
    movies = Movie.objects.filter(is_active=True).order_by('-release_date')
    
    # Get filters from request (e.g., /movies/?genre=action)
    query = request.GET.get('q', '') # General search query
    
    # 1. Search Query
    
    if query:
        movies = movies.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(director__icontains=query) |
            Q(cast__icontains=query)
        )
    
    # Get user's wishlist and interests if logged in
    user_wishlist = set()
    user_interests = set()
    if request.user.is_authenticated:
        user_wishlist = set(Wishlist.objects.filter(user=request.user).values_list('movie_id', flat=True))
        user_interests = set(Interest.objects.filter(user=request.user).values_list('movie_id', flat=True))

    context = {
        'movies': movies,
        'genres': Genre.objects.all(),
        'languages': Language.objects.all(),
        'selected_genre': request.GET.get('genre', ''),
        'selected_language': request.GET.get('language', ''),
        'query': query,
        'user_wishlist': user_wishlist,
        'user_interests': user_interests,
    }
    
    return render(request, 'movies/movie_list.html', context)


# ========== MOVIE DETAIL VIEW ==========
# Cache for 10 minutes, monitor performance
@cache_page(timeout=600)
@PerformanceMonitor.measure_performance
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
    
    in_wishlist = False
    is_interested = False
    user_review = None
    user_wishlist = set()
    user_interests = set()
    
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, movie=movie).exists()
        is_interested = Interest.objects.filter(user=request.user, movie=movie).exists()
        user_review = Review.objects.filter(user=request.user, movie=movie).first()
        user_wishlist = set(Wishlist.objects.filter(user=request.user).values_list('movie_id', flat=True))
        user_interests = set(Interest.objects.filter(user=request.user).values_list('movie_id', flat=True))

    # Get reviews for this movie
    reviews = Review.objects.filter(movie=movie).order_by('-created_at')

    # Get recommended movies (same genre, excluding current)
    recommended_movies = Movie.objects.filter(
        genres__in=movie.genres.all(),
        is_active=True
    ).exclude(id=movie.id).distinct()[:4]

    # Get recently added movies
    recently_added = Movie.objects.filter(is_active=True).order_by('-created_at').exclude(id=movie.id)[:4]

    context = {
        'movie': movie,
        'cities_with_showtimes': cities_with_showtimes,
        'genres': movie.genres.all(),
        'in_wishlist': in_wishlist,
        'is_interested': is_interested,
        'reviews': reviews,
        'user_review': user_review,
        'recommended_movies': recommended_movies,
        'recently_added': recently_added,
        'user_wishlist': user_wishlist,
        'user_interests': user_interests,
    }
    
    return render(request, 'movies/movie_detail.html', context)

# ========== HOME PAGE VIEW ==========
# Cache for 10 minutes, monitor performance
@cache_page(timeout=600)
@PerformanceMonitor.measure_performance
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
    
    # Get user's wishlist and interests if logged in
    user_wishlist = set()
    user_interests = set()
    if request.user.is_authenticated:
        user_wishlist = set(Wishlist.objects.filter(user=request.user).values_list('movie_id', flat=True))
        user_interests = set(Interest.objects.filter(user=request.user).values_list('movie_id', flat=True))
    
    context = {
        'featured_movies': featured_movies,
        'now_showing': now_showing,
        'genres': genres,
        'user_wishlist': user_wishlist,
        'user_interests': user_interests,
    }
    
    return render(request, 'movies/home.html', context)








# ========== MOVIE TRAILER VIEW ==========
# Cache for 15 minutes (trailers don't change often)
@cache_page(timeout=900)
@PerformanceMonitor.measure_performance
def movie_trailer(request, slug):
    """Movie detail page with embedded trailer"""
    movie = get_object_or_404(Movie, slug=slug, is_active=True)
    
    # Get trailer backend
    trailer = None
    if movie.trailer_url:
        backend = detect_backend(movie.trailer_url)
        trailer = {
            'url': movie.trailer_url,
            'backend': backend,
            'youtube_id': movie.youtube_id,
        }
    
    # Get showtimes
    showtimes = Showtime.objects.filter(
        movie=movie,
        is_active=True,
        date__gte=timezone.now().date()
    ).order_by('date', 'start_time')[:10]
    
    # Get reviews
    reviews = Review.objects.filter(movie=movie).order_by('-created_at')[:5]
    
    # Check if user has reviewed
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(user=request.user, movie=movie).first()
    
    # Check if in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, movie=movie).exists()
    
    context = {
        'movie': movie,
        'trailer': trailer,
        'showtimes': showtimes,
        'reviews': reviews,
        'user_review': user_review,
        'in_wishlist': in_wishlist,
        'genres': movie.genres.all(),
    }
    
    return render(request, 'movies/movie_trailer.html', context)



# Create rate limiters for different actions
wishlist_limiter = RateLimiter(rate='30/m', key_prefix='wishlist')  # 30 actions per minute
review_limiter = RateLimiter(rate='5/m', key_prefix='review')  # 5 reviews per minute


@login_required
@wishlist_limiter.rate_limit_view
def toggle_wishlist(request, movie_id):
    """Add/remove movie from wishlist"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    if request.method == 'POST':
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            movie=movie
        )
        
        if not created:
            wishlist_item.delete()
            message = f'Removed {movie.title} from wishlist'
            action = 'removed'
        else:
            message = f'Added {movie.title} to wishlist'
            action = 'added'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'action': action,
                'message': message,
                'wishlist_count': movie.wishlist_count,
            })
        
        messages.success(request, message)
        return redirect('movie_detail', slug=movie.slug)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@wishlist_limiter.rate_limit_view
def toggle_interest(request, movie_id):
    """Add/remove movie from interest list"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    if request.method == 'POST':
        interest_item, created = Interest.objects.get_or_create(
            user=request.user,
            movie=movie
        )
        
        if not created:
            interest_item.delete()
            message = f'No longer interested in {movie.title}'
            action = 'removed'
        else:
            message = f'Marked {movie.title} as interested'
            action = 'added'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'action': action,
                'message': message,
                'interest_count': movie.interest_count,
            })
        
        messages.success(request, message)
        return redirect('movie_detail', slug=movie.slug)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def wishlist_view(request):
    """User's wishlist"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('movie')
    
    user_wishlist = set(wishlist_items.values_list('movie_id', flat=True))
    
    context = {
        'wishlist_items': wishlist_items,
        'user_wishlist': user_wishlist,
    }
    
    return render(request, 'movies/wishlist.html', context)

# ========== REVIEW VIEWS ==========
@login_required
@review_limiter.rate_limit_view
@PerformanceMonitor.measure_performance
def add_review(request, movie_id):
    """Add or update review"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if not all([rating, title, content]):
            messages.error(request, '❌ Please fill in all fields: rating, headline, and review content.')
            return redirect('movie_detail', slug=movie.slug)
        
        # Create or update review
        review, created = Review.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={
                'rating': rating,
                'title': title,
                'content': content,
            }
        )
        
        if created:
            messages.success(request, f'🎉 Thanks for your review! Your {rating}/10 rating for "{movie.title}" has been posted.')
        else:
            messages.success(request, f'✅ Review updated! Your new {rating}/10 rating for "{movie.title}" has been saved.')
        
        return redirect('movie_detail', slug=movie.slug)
    
    return redirect('movie_trailer', slug=movie.slug)

@csrf_exempt
@login_required
@wishlist_limiter.rate_limit_view
def like_review(request, review_id):
    """Like or dislike a review"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            review = Review.objects.get(id=review_id)
            is_like = data.get('is_like', True)
            
            # Check if user already liked/disliked
            existing_like = ReviewLike.objects.filter(
                user=request.user,
                review=review
            ).first()
            
            if existing_like:
                if existing_like.is_like == is_like:
                    # Remove like/dislike
                    existing_like.delete()
                    if is_like:
                        review.likes -= 1
                    else:
                        review.dislikes -= 1
                    action = 'removed'
                else:
                    # Change like to dislike or vice versa
                    existing_like.is_like = is_like
                    existing_like.save()
                    if is_like:
                        review.likes += 1
                        review.dislikes -= 1
                    else:
                        review.likes -= 1
                        review.dislikes += 1
                    action = 'changed'
            else:
                # New like/dislike
                ReviewLike.objects.create(
                    user=request.user,
                    review=review,
                    is_like=is_like
                )
                if is_like:
                    review.likes += 1
                else:
                    review.dislikes += 1
                action = 'added'
            
            review.save()
            return JsonResponse({
                'success': True,
                'action': action,
                'likes': review.likes,
                'dislikes': review.dislikes
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# ========== AUTOCOMPLETE API ==========
# Rate limit autocomplete to prevent abuse
@api_limiter.rate_limit_view
def movie_autocomplete(request):
    """Autocomplete for search"""
    query = request.GET.get('q', '')
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    # Cache autocomplete results
    cache_key = f'autocomplete_{query.lower()}'
    results = cache.get(cache_key)
    
    if not results:
        movies = Movie.objects.filter(
            Q(title__icontains=query) |
            Q(cast__icontains=query) |
            Q(director__icontains=query),
            is_active=True
        )[:10]
        
        results = [
            {
                'id': movie.id,
                'title': movie.title,
                'year': movie.release_date.year,
                'rating': movie.rating,
                'poster_url': movie.poster.url if movie.poster else '',
                'url': movie.get_absolute_url(),
            }
            for movie in movies
        ]
        
        cache.set(cache_key, results, timeout=300)  # Cache for 5 minutes
    
    return JsonResponse({'results': results})

# ========== YOUTUBE TRAILER SEARCH (Optional) ==========
def search_youtube_trailer(request, movie_id):
    """Search YouTube for movie trailer (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    movie = get_object_or_404(Movie, id=movie_id)
    
    import requests
    
    search_query = f"{movie.title} {movie.release_date.year} official trailer"
    api_key = settings.YOUTUBE_API_KEY
    
    if not api_key:
        return JsonResponse({'error': 'YouTube API key not configured'})
    
    try:
        # Search YouTube
        url = f"https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': search_query,
            'key': api_key,
            'maxResults': 5,
            'type': 'video',
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        videos = []
        for item in data.get('items', []):
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            thumbnail = item['snippet']['thumbnails']['high']['url']
            
            videos.append({
                'video_id': video_id,
                'title': title,
                'thumbnail': thumbnail,
                'url': f'https://www.youtube.com/watch?v={video_id}',
            })
        
        return JsonResponse({'videos': videos})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def toggle_wishlist_json(request):
    """Toggle wishlist via JSON API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            movie_id = data.get('movie_id')
            movie = get_object_or_404(Movie, id=movie_id)
            
            wishlist_item, created = Wishlist.objects.get_or_create(
                user=request.user,
                movie=movie
            )
            
            if not created:
                wishlist_item.delete()
                return JsonResponse({
                    'success': True,
                    'action': 'removed',
                    'in_wishlist': False,
                })
            
            return JsonResponse({
                'success': True,
                'action': 'added',
                'in_wishlist': True,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@csrf_exempt
def toggle_interest_json(request):
    """Toggle interest via JSON API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            movie_id = data.get('movie_id')
            movie = get_object_or_404(Movie, id=movie_id)
            
            interest_item, created = Interest.objects.get_or_create(
                user=request.user,
                movie=movie
            )
            
            if not created:
                interest_item.delete()
                return JsonResponse({
                    'success': True,
                    'action': 'removed',
                    'is_interested': False,
                })
            
            return JsonResponse({
                'success': True,
                'action': 'added',
                'is_interested': True,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)