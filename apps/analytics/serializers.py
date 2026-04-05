"""
Serializers for the analytics app.
"""

from rest_framework import serializers
from .models import EventTracking, ProviderAnalytics, PlatformAnalytics, GovernorateAnalytics


class EventTrackingSerializer(serializers.ModelSerializer):
    """
    Serializer for EventTracking model.
    """
    class Meta:
        model = EventTracking
        fields = [
            'event_type', 'content_type', 'object_id', 'metadata',
            'governorate', 'center'
        ]


class ProviderAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for ProviderAnalytics model.
    """
    class Meta:
        model = ProviderAnalytics
        fields = [
            'date', 'profile_views', 'service_views', 'service_clicks',
            'messages_received', 'messages_sent', 'response_time_minutes',
            'inquiries_count', 'bookings_count', 'conversion_rate',
            'revenue', 'total_views', 'average_rating'
        ]


class PlatformAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for PlatformAnalytics model.
    """
    class Meta:
        model = PlatformAnalytics
        fields = [
            'date', 'total_users', 'new_users', 'active_users', 'verified_users',
            'total_services', 'new_services', 'approved_services', 'approval_rate',
            'page_views', 'service_views', 'searches', 'messages',
            'total_revenue', 'commission_revenue'
        ]


class GovernorateAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for GovernorateAnalytics model.
    """
    governorate_name = serializers.CharField(source='governorate.name_ar', read_only=True)
    
    class Meta:
        model = GovernorateAnalytics
        fields = [
            'governorate_name', 'date', 'services_count', 'providers_count',
            'bookings_count', 'revenue'
        ]