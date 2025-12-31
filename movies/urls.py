from django.urls import path
from . import views

# ==============================================================================
# ❓ URL CONFIGURATION
# This file maps URL paths (what you type in the browser) to Views (Python functions).
# Django reads this list from top to bottom and stops at the first match.
# ==============================================================================

urlpatterns = [
    # 1. Home Page: Matches empty string 'http://website.com/'
    #    name='home' allows us to use {% url 'home' %} in HTML templates.
    path('', views.home, name='home'),
    
    # 2. Movie List: Matches 'http://website.com/movies/'
    path('movies/', views.movie_list, name='movie_list'),

    
    # 3. Movie Detail: Matches 'http://website.com/movies/some-movie-name/'
    #    <slug:slug> is a Path Converter. It "captures" the part of the URL 
    #    and passes it as an argument named 'slug' to the 'movie_detail' view function.
    #    'slug' matches letters, numbers, hyphens, and underscores.
    path('movies/<slug:slug>/', views.movie_detail, name='movie_detail'),
    
    # Movie trailer
    path('movie/<slug:slug>/trailer/', views.movie_trailer, name='movie_trailer'),
    
    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('<int:movie_id>/wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
    path('<int:movie_id>/interest/toggle/', views.toggle_interest, name='toggle_interest'),
    
    # Reviews
    path('movie/<int:movie_id>/review/add/', views.add_review, name='add_review'),
    path('review/<int:review_id>/like/', views.like_review, name='like_review'),
    
    # Autocomplete
    path('autocomplete/', views.movie_autocomplete, name='movie_autocomplete'),
    
    # YouTube search (admin)
    path('movie/<int:movie_id>/youtube-search/', views.search_youtube_trailer, name='search_youtube_trailer'),
]