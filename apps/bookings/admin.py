"""
Admin configuration for bookings app.
"""

from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Admin interface for Booking model.
    """
    list_display = ('customer', 'service', 'status', 'scheduled_date', 'total_amount')
    list_filter = ('status', 'scheduled_date')
    search_fields = ('customer__first_name', 'customer__last_name', 'service__title_ar')
    raw_id_fields = ('customer', 'service')