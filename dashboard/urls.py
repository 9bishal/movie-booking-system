# dashboard/urls.py
# ------------------------------------------------------------
# URL configuration for the admin dashboard.
# All routes are prefixed with 'admin/dashboard/' to integrate
# seamlessly with Django's built‑in admin site without URL clashes.
# ------------------------------------------------------------

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard main pages
    path('admin/dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    path('admin/dashboard/reports/', views.analytics_dashboard, name='reports_dashboard'),

    # API endpoints for charts and real‑time data
    path('admin/dashboard/api/revenue-data/', views.revenue_data, name='revenue_data'),
    path('admin/dashboard/api/user-activity/', views.user_activity_data, name='user_activity'),
    path('admin/dashboard/api/movie-performance/', views.movie_performance_data, name='movie_performance'),
    path('admin/dashboard/api/theater-performance/', views.theater_performance_data, name='theater_performance'),
    path('admin/dashboard/api/realtime-stats/', views.realtime_stats, name='realtime_stats'),
    path('admin/dashboard/api/system-status/', views.system_status, name='system_status'),

    # CSV export endpoints
    path('admin/dashboard/export/bookings/', views.export_bookings_csv, name='export_bookings_csv'),
    path('admin/dashboard/export/revenue/', views.export_revenue_report, name='export_revenue_report'),
]