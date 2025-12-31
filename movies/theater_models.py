from django.db import models
from django.utils.text import slugify

# ========== CITY MODEL ==========
# Represents the cities where theaters are located.
class City(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        # 'verbose_name_plural' defines the correct plural name for the Admin panel.
        # Otherwise, Django would auto-pluralize "City" to "Citys".
        verbose_name_plural = 'cities'
        ordering = ['name']

# ========== THEATER MODEL ==========
# Represents a physical theater complex (e.g., "PVR Cyber Hub").
class Theater(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    
    # ForeignKey links each theater to exactly one city.
    # on_delete=models.CASCADE means if a City is deleted, all its Theaters are strictly deleted.
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    
    address = models.TextField()
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Amenities Flags
    has_parking = models.BooleanField(default=False)
    has_food_court = models.BooleanField(default=False)
    has_wheelchair_access = models.BooleanField(default=True)

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.city.name}"

    class Meta:
        ordering = ['city', 'name']


# ========== SCREEN MODEL ==========
# Represents a specific audi/screen inside a theater (e.g., "Audi 1", "IMAX Screen").
class Screen(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)  # Screen 1, Screen 2, etc.
    
    # Choices for screen types logic
    screen_type = models.CharField(max_length=20, choices=[
        ('2D', '2D'),
        ('3D', '3D'),
        ('IMAX', 'IMAX'),
        ('4DX', '4DX'),
    ], default='2D')
    
    total_seats = models.IntegerField(default=100)
    
    def __str__(self):
        return f"{self.theater.name} - {self.name} ({self.screen_type})"
    
    class Meta:
        ordering = ['theater', 'name']

# ========== SHOWTIME MODEL ==========
# The most complex model: links a Movie, a Screen, and a Time.
# This represents an actual show that users can book.
class Showtime(models.Model):
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE)
    
    # Date and Time are stored separately for easier filtering (e.g., "All shows today").
    # Alternatively, a single DateTimeField could be used.
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Pricing: Always use DecimalField for currency to avoid floating-point errors.
    price = models.DecimalField(max_digits=8, decimal_places=2, default=200.00)
    
    # Tracks how many seats are left. Logic will need to decrease this on booking.
    available_seats = models.IntegerField(default=100)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.movie.title} - {self.date} {self.start_time}"
    
    def get_formatted_time(self):
        """Format time for display (e.g., 09:30 PM)"""
        return self.start_time.strftime("%I:%M %p")
    
    def get_formatted_date(self):
        """Format date for display (e.g., 22 Dec, 2025)"""
        return self.date.strftime("%d %b, %Y")
    
    class Meta:
        ordering = ['date', 'start_time']