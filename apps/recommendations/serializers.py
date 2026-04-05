"""
Serializers for the recommendations app.
"""

from rest_framework import serializers
from .models import ServiceRecommendation, ProviderSentimentSummary
from apps.services.serializers import ServiceSerializer


class ServiceRecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for ServiceRecommendation model.
    """
    recommended_service = ServiceSerializer(read_only=True)
    
    class Meta:
        model = ServiceRecommendation
        fields = [
            'recommended_service', 'similarity_score', 'factors'
        ]


class ProviderSentimentSummarySerializer(serializers.ModelSerializer):
    """
    Serializer for ProviderSentimentSummary model.
    """
    class Meta:
        model = ProviderSentimentSummary
        fields = [
            'period_start', 'period_end', 'positive_count', 'neutral_count',
            'negative_count', 'total_reviews', 'punctuality_score',
            'quality_score', 'communication_score', 'value_score'
        ]