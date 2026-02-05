from django.contrib import admin
from .models import Movie, Genre, Language
from .theater_models import City, Theater, Screen, Showtime
from django.utils.html import format_html

# ==============================================================================
# ❓ WHY THIS FILE EXISTS:
# This file is used to configure the Django Admin Panel (the built-in superuser interface).
# By registering models here, we can Create, Read, Update, and Delete (CRUD) data
# directly from the web browser without writing SQL or custom forms.
# ==============================================================================

# ❓ WHY USE @admin.register?
# This 'decorator' tells Django: "Connect the Class below to the Genre model."
# It's a shortcut. The alternative would be writing `admin.site.register(Genre, GenreAdmin)`.
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    # ❓ WHY list_display?
    # Controls which columns are shown in the main table list of Genres.
    # Without this, you'd only see the "__str__" representation of the object.
    list_display = ['name', 'slug', 'icon']
    
    # ❓ WHY prepopulated_fields?
    # Usability feature! When you type in the 'name' field, JavaScript automatically
    # types the URL-friendly version into the 'slug' field.
    prepopulated_fields = {'slug': ('name',)}
    
    # ❓ WHY search_fields?
    # Adds a search bar at the top of the list to find genres by name.
    search_fields = ['name']

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    # Shows these columns in the Movie list
    list_display = ['title', 'release_date', 'rating', 'duration_formatted', 'is_active', 'poster_preview']
    
    # ❓ WHY list_filter?
    # Adds a sidebar on the right to quickly filter movies (e.g., "Show only Action movies" or "Show only Active movies").
    list_filter = ['genres', 'language', 'is_active', 'release_date']
    
    # Search functionality
    search_fields = ['title', 'director', 'cast']
    
    # Auto-fill slug from title
    prepopulated_fields = {'slug': ('title',)}
    
    # ❓ WHY filter_horizontal? 
    # "Genres" is a ManyToMany field. By default, Django shows a clunky multi-select box.
    # filter_horizontal provides a much better UI with two boxes ("Available" vs "Chosen") 
    # and a search filter inside.
    filter_horizontal = ['genres']
    
    # ❓ WHY fieldsets?
    # Organizes the form fields into logical sections/tabs.
    # Instead of one giant list of 20 fields, we group them into "Basic Info", "Details", etc.
    fieldsets = [
        ('Basic Info', {
            'fields': ['title', 'slug', 'description', 'poster', 'trailer_url']
        }),
        ('Details', {
            'fields': ['release_date', 'duration', 'certificate', 'rating', 'genres', 'language']
        }),
        ('Cast & Crew', {
            'fields': ['director', 'cast']
        }),
        ('Status', {
            'fields': ['is_active']
        }),
    ]
    
    class Media:
        css = {
            'all': ('admin/css/movie_admin.css',)
        }
    
    # ❓ WHY THIS METHOD?
    # Keeps the admin list clean. This method simply calls the helper we defined in the Model.
    def duration_formatted(self, obj):
        return obj.duration_formatted()
    duration_formatted.short_description = 'Duration'  # Sets the column header name
    
    # ❓ WHY format_html?
    # By default, Django escapes HTML (shows "<img>" as text) for security.
    # format_html marks the string as safe, so the browser renders the actual image.
    def poster_preview(self, obj):
        if obj.poster:
            return format_html(
                '<img src="{}" style="width: 50px; height: 75px; object-fit: cover; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />', 
                obj.poster.url
            )
        return format_html('<div style="width: 50px; height: 75px; background: #f0f0f0; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #999;">No Poster</div>')
    poster_preview.short_description = 'Poster'

# ========== CITY ADMIN ==========
@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active']

# ========== THEATER ADMIN ==========
@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'has_parking', 'has_food_court', 'is_active']
    # ❓ WHY filter by has_parking?
    # Helps admins quickly find theaters with specific amenities.
    list_filter = ['city', 'is_active', 'has_parking', 'has_food_court']
    search_fields = ['name', 'address']
    prepopulated_fields = {'slug': ('name',)}

# ========== SCREEN ADMIN ==========
@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ['name', 'theater', 'screen_type', 'total_seats']
    list_filter = ['theater', 'screen_type']
    
    # ❓ WHY search 'theater__name'?
    # 'theater' is a foreign key. We can't search an object ID efficiently.
    # This syntax tells Django to look up the 'name' field of the related Theater object.
    search_fields = ['name', 'theater__name']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "theater":
            # Show theater with city in dropdown
            kwargs["queryset"] = Theater.objects.select_related('city').all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# ========== SHOWTIME ADMIN ==========
@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ['movie', 'screen', 'date', 'start_time', 'price', 'available_seats', 'is_active']
    list_filter = ['date', 'is_active', 'screen__theater__city']
    
    # Search by movie title or screen name
    search_fields = ['movie__title', 'screen__name']
    
    # ❓ WHY date_hierarchy?
    # Adds a navigation bar at the top to drill down by Year > Month > Day.
    # Extremely useful for finding showtimes efficiently.
    date_hierarchy = 'date'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "screen":
            # Show screen with theater and city details in dropdown
            kwargs["queryset"] = Screen.objects.select_related('theater__city').all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)