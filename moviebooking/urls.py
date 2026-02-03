from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
def home_redirect(request):
    """Redirect root to login page"""
    return redirect('login')

urlpatterns = [
    # Custom Admin
    path('custom-admin/', include('custom_admin.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('bookings/', include('bookings.urls')),
    path('', include('movies.urls')),  # Include movies app URLs (handles home page)
]

# .Serve media files and Debug Toolbar in development
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Serve media files in production too
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)