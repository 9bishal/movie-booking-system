from django.db import models
from django.utils.text import slugify

from embed_video.fields import EmbedVideoField
# ========== GENRE MODEL ==========
# This model acts as a lookup table for movie genres.
# Using a separate model allows us to manage genres dynamically in the Admin panel.
class Genre(models.Model):
    """Movie genres like Action, Comedy, Drama"""
    name = models.CharField(max_length=100)
    
    # A 'slug' is a URL-friendly version of the name (e.g., 'Action Thriller' -> 'action-thriller').
    # We use it in URLs instead of IDs for better SEO and readability.
    slug = models.SlugField(max_length=100, unique=True)
    
    # Store the FontAwesome icon class string (e.g., 'fas fa-film') to render icons in templates
    icon = models.CharField(max_length=50, default="fas fa-film")
    
    # Override the save method to automatically generate a slug from the name if one isn't provided.
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

# ========== LANGUAGE MODEL ==========
# Simple lookup table for languages to ensure data consistency
# (e.g., prevents mixing 'English', 'english', 'Eng').
class Language(models.Model):
    """Movie languages like Hindi, English, Tamil"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)  # ISO code like 'hi', 'en'
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

# ========== MOVIE MODEL ==========
# The core model representing a movie entity.
class Movie(models.Model):
    """Main movie model"""
    title = models.CharField(max_length=200)
    # Unique slug for SEO-friendly movie detail URLs (e.g., /movies/titanic-1997/)
    slug = models.SlugField(max_length=200, unique=True)
    
    description = models.TextField()
    duration = models.IntegerField(help_text="Duration in minutes")
    release_date = models.DateField()
    
    # Choices allow us to restrict the input to a specific set of values.
    # The first value in the tuple is stored in DB, second is displayed in forms.
    certificate = models.CharField(max_length=10, choices=[
        ('U', 'U - Universal'),
        ('UA', 'UA - Parental Guidance'),
        ('A', 'A - Adults Only'),
        ('R', 'R - Restricted'),
    ], default='UA')
    
    status = models.CharField(max_length=20, choices=[
        ('now_showing', 'Now Showing'),
        ('coming_soon', 'Coming Soon'),
        ('expired', 'Expired'),
    ], default='now_showing')

    rating = models.FloatField(default=0.0)  # IMDb style rating
    
    # ImageField requires the 'Pillow' library. 'upload_to' defines the subdirectory in MEDIA_ROOT.
    poster = models.ImageField(upload_to='movie_posters/', blank=True, null=True)
    
    trailer_url = models.URLField(blank=True)  # YouTube URL
    
    # RELATIONSHIPS:
    # ManyToManyField: A movie can have multiple genres, and a genre can belong to multiple movies.
    # Django creates a hidden intermediate table to manage this many-to-many link.
    genres = models.ManyToManyField(Genre, related_name='movies')
    
    # ForeignKey: A movie has one primary language (One-to-Many relationship).
    # on_delete=models.SET_NULL means if a Language is deleted, the movie keeps existing 
    # but its language field becomes NULL (instead of deleting the movie).
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, related_name='movies')
    
    # Additional info
    director = models.CharField(max_length=200, blank=True)
    
    # In a production app, Cast might be a separate model with M2M relationship.
    # For simplicity here, we stick to a text field.
    cast = models.TextField(blank=True, help_text="Comma separated list of actors")
    
    # Status fields for internal management
    is_active = models.BooleanField(default=True)  # Soft delete logic: hide instead of delete
    created_at = models.DateTimeField(auto_now_add=True)  # Set once on creation
    updated_at = models.DateTimeField(auto_now=True)      # Updated every time save() is called
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} ({self.release_date.year})"
    
    # Helper method to display duration nicely in templates
    def duration_formatted(self):
        """Convert minutes to hours and minutes (e.g., 150 -> 2h 30m)"""
        hours = self.duration // 60
        minutes = self.duration % 60
        return f"{hours}h {minutes}m"
    
    def get_genres_list(self):
        """Return comma separated genres string for display"""
        return ", ".join([genre.name for genre in self.genres.all()])

    # Add rating count
    rating_count = models.IntegerField(default=0)
    total_rating = models.FloatField(default=0.0)

    @property
    def youtube_id(self):
        import re
        pattern = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
        match = re.search(pattern, self.trailer_url)
        if match:
            return match.group(1)
        return None 

    def update_rating(self, new_rating):
        self.total_rating += new_rating
        self.rating_count += 1
        self.rating = self.total_rating / self.rating_count
        self.save()

    def get_average_rating(self):
        """Get average rating with one decimal"""
        if self.rating_count > 0:
            return round(self.total_rating / self.rating_count, 1)
        return 0.0
    def get_rating_percentage(self):
        """Get rating as percentage for stars"""
        return (self.rating / 10) * 100 if self.rating else 0

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('movie_detail', kwargs={'slug': self.slug})

    # DISABLED: Wishlist feature commented out
    # @property
    # def wishlist_count(self):
    #     """Return the number of times this movie is in wishlists"""
    #     return self.wishlisted_by.count()

    # DISABLED: Interest feature commented out
    # @property
    # def interest_count(self):
    #     """Return the number of times this movie is marked as interested"""
    #     return self.interests.count()

    class Meta:
        # Default ordering: Newest releases first, then alphabetical by title
        ordering = ['-release_date', 'title']