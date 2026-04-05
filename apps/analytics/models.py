"""
Analytics models for Egyptian Service Marketplace.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from apps.core.models import BaseModel, Province, City
from apps.services.models import Service

User = get_user_model()


class EventTracking(BaseModel):
    """
    Track user events for analytics.
    """
    EVENT_TYPE_CHOICES = [
        ('page_view', _('Page View')),
        ('service_view', _('Service View')),
        ('service_click', _('Service Click')),
        ('profile_view', _('Profile View')),
        ('search', _('Search')),
        ('filter_apply', _('Filter Applied')),
        ('message_sent', _('Message Sent')),
        ('booking_attempt', _('Booking Attempt')),
        ('contact_provider', _('Contact Provider')),
        ('service_share', _('Service Shared')),
        ('favorite_add', _('Added to Favorites')),
        ('review_submit', _('Review Submitted')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    session_id = models.CharField(_('Session ID'), max_length=40, blank=True)
    event_type = models.CharField(_('Event type'), max_length=20, choices=EVENT_TYPE_CHOICES)
    
    # Generic foreign key for target object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey('content_type', 'object_id')
    
    # Event metadata
    metadata = models.JSONField(_('Event metadata'), default=dict)
    ip_address = models.GenericIPAddressField(_('IP Address'))
    user_agent = models.TextField(_('User Agent'), blank=True)
    referrer = models.URLField(_('Referrer'), blank=True)
    
    # Location data
    governorate = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    center = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Event Tracking')
        verbose_name_plural = _('Event Tracking')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.user or 'Anonymous'}"


class ProviderAnalytics(BaseModel):
    """
    Pre-aggregated analytics for providers.
    """
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    date = models.DateField(_('Date'))
    
    # Profile metrics
    profile_views = models.PositiveIntegerField(_('Profile views'), default=0)
    service_views = models.PositiveIntegerField(_('Service views'), default=0)
    service_clicks = models.PositiveIntegerField(_('Service clicks'), default=0)
    
    # Engagement metrics
    messages_received = models.PositiveIntegerField(_('Messages received'), default=0)
    messages_sent = models.PositiveIntegerField(_('Messages sent'), default=0)
    response_time_minutes = models.FloatField(_('Avg response time (minutes)'), default=0)
    
    # Conversion metrics
    inquiries_count = models.PositiveIntegerField(_('Inquiries'), default=0)
    bookings_count = models.PositiveIntegerField(_('Bookings'), default=0)
    conversion_rate = models.FloatField(_('Conversion rate'), default=0)
    
    # Revenue metrics (placeholder for payments)
    revenue = models.DecimalField(
        _('Revenue'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Rating metrics
    total_views = models.PositiveIntegerField(_('Reviews count'), default=0)
    average_rating = models.FloatField(_('Average rating'), default=0)

    class Meta:
        verbose_name = _('Provider Analytics')
        verbose_name_plural = _('Provider Analytics')
        unique_together = ['provider', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.provider.full_name} - {self.date}"


class PlatformAnalytics(BaseModel):
    """
    Platform-wide analytics aggregations.
    """
    date = models.DateField(_('Date'))
    
    # User metrics
    total_users = models.PositiveIntegerField(_('Total users'), default=0)
    new_users = models.PositiveIntegerField(_('New users'), default=0)
    active_users = models.PositiveIntegerField(_('Active users'), default=0)
    verified_users = models.PositiveIntegerField(_('Verified users'), default=0)
    
    # Service metrics
    total_services = models.PositiveIntegerField(_('Total services'), default=0)
    new_services = models.PositiveIntegerField(_('New services'), default=0)
    approved_services = models.PositiveIntegerField(_('Approved services'), default=0)
    approval_rate = models.FloatField(_('Approval rate'), default=0)
    
    # Engagement metrics
    page_views = models.PositiveIntegerField(_('Page views'), default=0)
    service_views = models.PositiveIntegerField(_('Service views'), default=0)
    searches = models.PositiveIntegerField(_('Searches'), default=0)
    messages = models.PositiveIntegerField(_('Messages'), default=0)
    
    # Revenue metrics (placeholder)
    total_revenue = models.DecimalField(
        _('Total revenue'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    commission_revenue = models.DecimalField(
        _('Commission revenue'),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    class Meta:
        verbose_name = _('Platform Analytics')
        verbose_name_plural = _('Platform Analytics')
        unique_together = ['date']
        ordering = ['-date']

    def __str__(self):
        return f"Platform Analytics - {self.date}"


class GovernorateAnalytics(BaseModel):
    """
    Analytics by Egyptian governorate.
    """
    governorate = models.ForeignKey(
        Province,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    date = models.DateField(_('Date'))
    
    # Service metrics
    services_count = models.PositiveIntegerField(_('Services count'), default=0)
    providers_count = models.PositiveIntegerField(_('Providers count'), default=0)
    bookings_count = models.PositiveIntegerField(_('Bookings count'), default=0)
    
    # Revenue metrics
    revenue = models.DecimalField(
        _('Revenue'),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    class Meta:
        verbose_name = _('Governorate Analytics')
        verbose_name_plural = _('Governorate Analytics')
        unique_together = ['governorate', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.governorate.name_ar} - {self.date}"