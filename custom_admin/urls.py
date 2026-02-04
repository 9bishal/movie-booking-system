from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    # Authentication
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('movies/', views.movie_management, name='movie_management'),
    
    # API Endpoints
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/revenue/', views.api_revenue, name='api_revenue'),
    path('api/bookings/', views.api_bookings, name='api_bookings'),
    path('api/theaters/', views.api_theaters, name='api_theaters'),
]
