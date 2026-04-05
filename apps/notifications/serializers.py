"""
Serializers for the notifications app.
"""

from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title_ar', 'title_en',
            'message_ar', 'message_en', 'is_read', 'read_at', 'created_at'
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationPreference model.
    """
    class Meta:
        model = NotificationPreference
        fields = [
            'email_messages', 'email_bookings', 'email_reviews', 'email_payments',
            'email_marketing', 'sms_bookings', 'sms_payments', 'sms_urgent',
            'push_messages', 'push_bookings', 'push_reviews'
        ]