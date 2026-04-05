"""
Serializers for the reviews app.
"""

from rest_framework import serializers
from .models import Review, ReviewHelpfulness
from apps.accounts.serializers import UserSerializer


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model.
    """
    reviewer = UserSerializer(read_only=True)
    service_title = serializers.CharField(source='service.title_ar', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'service', 'service_title', 'reviewer', 'rating', 'title',
            'comment', 'provider_response', 'responded_at', 'helpful_count',
            'unhelpful_count', 'created_at'
        ]
        read_only_fields = ['reviewer', 'helpful_count', 'unhelpful_count', 'provider_response', 'responded_at']


class ReviewHelpfulnessSerializer(serializers.ModelSerializer):
    """
    Serializer for ReviewHelpfulness model.
    """
    class Meta:
        model = ReviewHelpfulness
        fields = ['id', 'review', 'vote', 'created_at']