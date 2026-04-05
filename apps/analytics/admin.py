from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from .models import (
    EventTracking,
    ProviderAnalytics,
    PlatformAnalytics,
    GovernorateAnalytics,
)


@admin.register(EventTracking)
class EventTrackingAdmin(admin.ModelAdmin):
    list_display = (
        'event_type',
        'user',
        'session_id',
        'content_type',
        'object_id',
        'governorate',
        'center',
        'created_at',
    )
    list_filter = (
        'event_type',
        'governorate',
        'created_at',
        'content_type',
    )
    search_fields = (
        'user__email',
        'user__username',
        'session_id',
        'ip_address',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    ordering = ('-created_at',)
    list_per_page = 50

    fieldsets = (
        ('Event Info', {
            'fields': (
                'event_type',
                'user',
                'session_id',
            )
        }),
        ('Target Object', {
            'fields': (
                'content_type',
                'object_id',
            )
        }),
        ('Metadata', {
            'fields': (
                'metadata',
                'ip_address',
                'user_agent',
                'referrer',
            )
        }),
        ('Location', {
            'fields': (
                'governorate',
                'center',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    def has_add_permission(self, request):
        # Prevent manual creation of events
        return False


@admin.register(ProviderAnalytics)
class ProviderAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'provider',
        'date',
        'profile_views',
        'service_views',
        'messages_received',
        'bookings_count',
        'conversion_rate',
        'revenue',
    )
    list_filter = (
        'date',
        'provider',
    )
    search_fields = (
        'provider__email',
        'provider__username',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    ordering = ('-date',)
    list_per_page = 25

    fieldsets = (
        ('Provider & Date', {
            'fields': ('provider', 'date')
        }),
        ('Profile Metrics', {
            'fields': (
                'profile_views',
                'service_views',
                'service_clicks',
            )
        }),
        ('Engagement Metrics', {
            'fields': (
                'messages_received',
                'messages_sent',
                'response_time_minutes',
            )
        }),
        ('Conversion Metrics', {
            'fields': (
                'inquiries_count',
                'bookings_count',
                'conversion_rate',
            )
        }),
        ('Revenue & Rating', {
            'fields': (
                'revenue',
                'total_views',
                'average_rating',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )


@admin.register(PlatformAnalytics)
class PlatformAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'total_users',
        'new_users',
        'active_users',
        'total_services',
        'page_views',
        'total_revenue',
    )
    list_filter = ('date',)
    ordering = ('-date',)
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    list_per_page = 25

    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('User Metrics', {
            'fields': (
                'total_users',
                'new_users',
                'active_users',
                'verified_users',
            )
        }),
        ('Service Metrics', {
            'fields': (
                'total_services',
                'new_services',
                'approved_services',
                'approval_rate',
            )
        }),
        ('Engagement Metrics', {
            'fields': (
                'page_views',
                'service_views',
                'searches',
                'messages',
            )
        }),
        ('Revenue', {
            'fields': (
                'total_revenue',
                'commission_revenue',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )


@admin.register(GovernorateAnalytics)
class GovernorateAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'governorate',
        'date',
        'services_count',
        'providers_count',
        'bookings_count',
        'revenue',
    )
    list_filter = (
        'governorate',
        'date',
    )
    ordering = ('-date',)
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    list_per_page = 25
