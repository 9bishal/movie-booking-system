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



actions=['confirm_booking', 'cancel_booking', 'expire_booking']
def confirm_payments(self, reques, queryset):
    updated=0
    for booking in queryset.filter(status="PENDING"):
        booking.marks_as_confirmed(f"MANUAL-{request.user.username}")
        updated+=1
    self.message_user(request, f"{updated} bookings confirmed successfully.")
confirm_payments.short_description = "Confirm selected bookings"



def cancel_bookings(self, request, queryset):
    """Cancel selected bookings"""
    updated = 0
    for booking in queryset.exclude(status='CANCELLED'):
        booking.status = 'CANCELLED'
        booking.save()
        updated += 1
    
    self.message_user(request, f'{updated} bookings cancelled successfully.')
cancel_bookings.short_description = "Cancel selected bookings"


def export_as_csv(self, request, queryset):
    import csv
    from django.http import HttpResponse
    response=HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="selected_bookings.csv"'
    writer=csv.writer(response)
    writer.writerow(['Booking ID', 'User', 'Movie', 'Amount', 'Status', 'Date'])    

    for booking in queryset:
        writer.writerow([
            booking.booking_number,
            booking.user.username,
            booking.showtime.movie.title,
            booking.total_amount,
            booking.status,
            booking.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    return response


export_as_csv.short_description = "Export selected bookings to CSV" 