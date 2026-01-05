from django.db import models
from django.contrib.auth.models import User
from movies.theater_models import Showtime
import uuid 
from django.utils import timezone
from decimal import Decimal

# ==============================================================================
# 💡 DATA MODELING CONCEPTS
# 1. JSONField: Allows storing flexible/unstructured data (like a list of seats)
#    inside a standard SQL database. Great for "NoSQL-like" features.
# 2. DecimalField: ALWAYS use this for money. FloatField has precision errors
#    (e.g., 0.1 + 0.2 != 0.3 in floating point math).
# 3. UUID: Universally Unique Identifier. Great for generating hard-to-guess
#    booking references (unlike 1, 2, 3...).
# ==============================================================================

class Booking(models.Model):
    BOOKING_STATUS=(
        ('PENDING', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
        ('FAILED', 'Failed'),
    )

    # ❓ WHY editable=False?
    # The booking number is generated system-side. Users/Admins shouldn't edit it manually.
    booking_number=models.CharField(max_length=20, unique=True, editable=False)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    showtime=models.ForeignKey(Showtime,on_delete=models.CASCADE)
    
    # ❓ why JSONField?
    # Because a booking can have any number of seats ["A1", "B2", "C3"].
    # Creating a separate "BookingSeat" model for every single seat is cleaner SQL,
    # but JSONField is faster for simple read-heavy operations like this.
    seats=models.JSONField() 
    total_seats=models.IntegerField(default=1)
    
    # Financial fields using DecimalField for precision
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    convenience_fee = models.DecimalField(max_digits=8, decimal_places=2, default=30.00)
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment Information
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='PENDING', db_index=True)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_id = models.CharField(max_length=100, blank=True, db_index=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, unique=True, db_index=True, null=True)
    
    # 🔐 Payment timeout protection
    payment_initiated_at = models.DateTimeField(null=True, blank=True)
    payment_received_at = models.DateTimeField(null=True, blank=True)
    refund_notification_sent = models.BooleanField(default=False, help_text="Track if refund notification email was sent")
    
    qr_code = models.ImageField(upload_to='booking_qrcodes/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering=['-created_at']

    def __str__(self):
        return f"{self.booking_number} - {self.user.username}"

    # ❓ CUSTOM SAVE METHOD
    # We override save() to automate logic *before* writing to DB.
    # 1. Generate unique Booking ID
    # 2. auto-calculate Taxes and Totals
    # 3. Set Expiry time for pending bookings
    def save(self, *args, **kwargs): # Fixed typo 'kwags' -> 'kwargs'
        if not self.booking_number:
            date_str=timezone.now().strftime('%Y%m%d')
            random_str=str(uuid.uuid4().int)[:5]
            self.booking_number=f"BOOK-{date_str}-{random_str}"


        if self.base_price and not self.tax_amount:
            self.tax_amount=(self.base_price+self.convenience_fee)*0.18
        
        if self.base_price and not self.total_amount:
            self.total_amount=self.base_price + self.convenience_fee + self.tax_amount
            
        if self.status == 'PENDING' and not self.expires_at:
            # Reserve seats based on settings timeout
            from django.conf import settings
            timeout = getattr(settings, 'SEAT_RESERVATION_TIMEOUT', 600)
            self.expires_at = timezone.now() + timezone.timedelta(seconds=timeout)
        
        super().save(*args, **kwargs)

    def get_seats_display(self):
        """Return seats as a comma-separated string"""
        if isinstance(self.seats, list):
            return ", ".join(self.seats)
        return str(self.seats)

    def get_formatted_total(self):
        return f"₹{self.total_amount:.2f}"

    def is_expired(self):
        """Check if booking has expired"""
        if self.status == 'PENDING' and self.expires_at:
            return timezone.now() > self.expires_at
        return False

# ========== TRANSACTION MODEL ==========
class Transaction(models.Model):
    """Payment transaction records"""
    TRANSACTION_STATUS = (
        ('INITIATED', 'Initiated'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    )
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='INITIATED')
    payment_gateway = models.CharField(max_length=50, default='RAZORPAY')
    gateway_response = models.JSONField(default=dict)  # Store gateway response
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.status}"