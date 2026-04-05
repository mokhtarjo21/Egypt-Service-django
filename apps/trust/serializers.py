"""
Serializers for the trust app.
"""

from rest_framework import serializers
from .models import Badge, UserBadge, TrustMetric


class BadgeSerializer(serializers.ModelSerializer):
    """
    Serializer for Badge model.
    """
    class Meta:
        model = Badge
        fields = [
            'id', 'name_ar', 'name_en', 'badge_type', 'description_ar',
            'description_en', 'icon', 'color', 'search_boost'
        ]


class UserBadgeSerializer(serializers.ModelSerializer):
    """
    Serializer for UserBadge model.
    """
    badge = BadgeSerializer(read_only=True)
    
    class Meta:
        model = UserBadge
        fields = [
            'id', 'badge', 'earned_at', 'expires_at', 'is_manual', 'notes'
        ]


class TrustMetricSerializer(serializers.ModelSerializer):
    """
    Serializer for TrustMetric model.
    """
    class Meta:
        model = TrustMetric
        fields = [
            'metric_type', 'value', 'period_start', 'period_end', 'calculation_date'
        ]