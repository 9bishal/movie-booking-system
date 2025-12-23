from django.contrib import admin
from .models import Booking, Transaction
from django.utils.html import format_html

# ==============================================================================
# 🔐 ADMIN SECURITY & USABILITY
# Admin classes control how models look in the backend dashboard.
# Important options for real-world apps:
# 1. readonly_fields: Prevent accidentally changing immutable data (like timestamps).
# 2. fieldsets: Organize long forms into logical groups.
# 3. format_html: Allow rendering safe HTML tags (like colored badges) in columns.
# ==============================================================================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_number', 'user', 'showtime', 'total_seats', 'total_amount', 'status', 'created_at', 'payment_status']
    list_filter = ['status', 'created_at', 'showtime__movie']
    search_fields = ['booking_number', 'user__username', 'showtime__movie__title']
    
    # ❓ WHY readonly?
    # Booking ID and timestamps are system-generated. Editing them manually destroys data integrity.
    readonly_fields = ['booking_number', 'created_at', 'confirmed_at']
    
    fieldsets = [
        ('Booking Information', {
            'fields': ['booking_number', 'user', 'showtime', 'seats', 'total_seats']
        }),
        ('Payment Information', {
            'fields': ['base_price', 'convenience_fee', 'tax_amount', 'total_amount', 'status', 'payment_method', 'payment_id']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'confirmed_at', 'expires_at']
        }),
    ]
    
    def payment_status(self, obj):
        colors = {
            'PENDING': 'warning',
            'CONFIRMED': 'success',
            'CANCELLED': 'danger',
            'EXPIRED': 'secondary',
            'FAILED': 'dark',
        }
        color = colors.get(obj.status, 'secondary')
        # format_html prevents XSS attacks by properly escaping unsafe characters
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.status)
    payment_status.short_description = 'Status'

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'booking', 'amount', 'status', 'payment_gateway', 'created_at']
    list_filter = ['status', 'payment_gateway', 'created_at']
    search_fields = ['transaction_id', 'booking__booking_number']
    readonly_fields = ['created_at']