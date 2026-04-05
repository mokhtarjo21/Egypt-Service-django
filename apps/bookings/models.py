"""
Booking models for Egyptian Service Marketplace.
Complete booking system implementation.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.core.models import BaseModel
from apps.services.models import Service

User = get_user_model()


class Booking(BaseModel):
    """
    Complete booking model for service reservations.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending Confirmation')),
        ('confirmed', _('Confirmed')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled_by_customer', _('Cancelled by Customer')),
        ('cancelled_by_provider', _('Cancelled by Provider')),
        ('refunded', _('Refunded')),
    ]

    CANCELLATION_REASON_CHOICES = [
        ('schedule_conflict', _('Schedule Conflict')),
        ('found_alternative', _('Found Alternative')),
        ('price_issue', _('Price Issue')),
        ('service_issue', _('Service Issue')),
        ('other', _('Other')),
    ]

    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_number = models.CharField(
        _('Booking Number'),
        max_length=20,
        unique=True,
        editable=False,
        default="TEMP",
        blank=True
    )
    
    # Relationships
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings_made',
        verbose_name=_('Customer')
    )
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings_received',
        verbose_name=_('Service Provider'),
        null=True
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('Service')
    )
    
    # Status and Scheduling
    status = models.CharField(
        _('Status'),
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending'
    )
    scheduled_date = models.DateTimeField(_('Scheduled Date'))
    scheduled_end_date = models.DateTimeField(
        _('Scheduled End Date'),
        null=True,
        blank=True
    )
    completed_at = models.DateTimeField(_('Completed at'), null=True, blank=True)
    
    # Pricing
    service_price = models.DecimalField(
        _('Service Price'),
        max_digits=10,
        decimal_places=2
    )
    additional_charges = models.DecimalField(
        _('Additional Charges'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    discount = models.DecimalField(
        _('Discount'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_amount = models.DecimalField(
        _('Total Amount'),
        max_digits=10,
        decimal_places=2
    )
    
    # Additional Information
    customer_notes = models.TextField(_('Customer Notes'), blank=True)
    provider_notes = models.TextField(_('Provider Notes'), blank=True)
    admin_notes = models.TextField(_('Admin Notes'), blank=True)
    
    # Location (if applicable)
    location_address = models.CharField(
        _('Service Location Address'),
        max_length=500,
        blank=True
    )
    location_governorate = models.CharField(
        _('Governorate'),
        max_length=100,
        blank=True
    )
    location_city = models.CharField(
        _('City'),
        max_length=100,
        blank=True
    )
    
    # Cancellation
    cancelled_at = models.DateTimeField(_('Cancelled at'), null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings_cancelled',
        verbose_name=_('Cancelled by')
    )
    cancellation_reason = models.CharField(
        _('Cancellation Reason'),
        max_length=30,
        choices=CANCELLATION_REASON_CHOICES,
        blank=True
    )
    cancellation_notes = models.TextField(_('Cancellation Notes'), blank=True)
    
    # Payment
    is_paid = models.BooleanField(_('Is Paid'), default=False)
    payment_method = models.CharField(
        _('Payment Method'),
        max_length=50,
        blank=True
    )
    
    # Refund
    is_refunded = models.BooleanField(_('Is Refunded'), default=False)
    refund_amount = models.DecimalField(
        _('Refund Amount'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    refunded_at = models.DateTimeField(_('Refunded at'), null=True, blank=True)

    class Meta:
        verbose_name = _('Booking')
        verbose_name_plural = _('Bookings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['provider', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['booking_number']),
        ]

    def __str__(self):
        return f"{self.booking_number} - {self.customer.full_name}"

    def save(self, *args, **kwargs):
        # Auto-generate booking number
        if not self.booking_number or self.booking_number == "TEMP":
            self.booking_number = self._generate_booking_number()
        
        # Set provider from service
        if not self.provider:
            self.provider = self.service.provider
        
        # Calculate total amount if not set
        if not self.total_amount or self.total_amount == 0:
            self.calculate_total()
        
        super().save(*args, **kwargs)

    def _generate_booking_number(self):
        """Generate unique booking number."""
        import random
        import string
        timestamp = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"BK{timestamp}{random_part}"

    def calculate_total(self):
        """Calculate total booking amount."""
        self.total_amount = (
            self.service_price + 
            self.additional_charges - 
            self.discount
        )
        return self.total_amount

    def can_be_cancelled(self):
        """Check if booking can be cancelled."""
        if self.status in ['completed', 'cancelled_by_customer', 'cancelled_by_provider', 'refunded']:
            return False
        
        # Can't cancel if less than 24 hours before scheduled time
        time_until_booking = self.scheduled_date - timezone.now()
        if time_until_booking.total_seconds() < 24 * 3600:
            return False
        
        return True

    def cancel(self, cancelled_by, reason='other', notes=''):
        """Cancel the booking."""
        if not self.can_be_cancelled():
            raise ValidationError(_('This booking cannot be cancelled.'))
        
        self.cancelled_at = timezone.now()
        self.cancelled_by = cancelled_by
        self.cancellation_reason = reason
        self.cancellation_notes = notes
        
        # Set status based on who cancelled
        if cancelled_by == self.customer:
            self.status = 'cancelled_by_customer'
        else:
            self.status = 'cancelled_by_provider'
        
        self.save()

    def confirm(self):
        """Confirm the booking."""
        if self.status != 'pending':
            raise ValidationError(_('Only pending bookings can be confirmed.'))
        
        self.status = 'confirmed'
        self.save()

    def start_service(self):
        """Mark service as started."""
        if self.status != 'confirmed':
            raise ValidationError(_('Only confirmed bookings can be started.'))
        
        self.status = 'in_progress'
        self.save()

    def complete(self):
        """Mark booking as completed."""
        if self.status not in ['confirmed', 'in_progress']:
            raise ValidationError(_('Only confirmed or in-progress bookings can be completed.'))
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def process_refund(self, refund_amount):
        """Process refund for cancelled booking."""
        if not self.status.startswith('cancelled'):
            raise ValidationError(_('Only cancelled bookings can be refunded.'))
        
        if self.is_refunded:
            raise ValidationError(_('This booking has already been refunded.'))
        
        self.is_refunded = True
        self.refund_amount = refund_amount
        self.refunded_at = timezone.now()
        self.status = 'refunded'
        self.save()

    @property
    def is_active(self):
        """Check if booking is active."""
        return self.status in ['pending', 'confirmed', 'in_progress']

    @property
    def can_be_reviewed(self):
        """Check if booking can be reviewed."""
        return self.status == 'completed' and not hasattr(self, 'review')