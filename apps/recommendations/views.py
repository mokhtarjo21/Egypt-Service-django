"""
Views for the recommendations app.
"""

from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import ServiceRecommendation, ProviderSentimentSummary
from .serializers import ServiceRecommendationSerializer, ProviderSentimentSummarySerializer


class ServiceRecommendationsView(generics.ListAPIView):
    """
    Get recommendations for a service.
    """
    serializer_class = ServiceRecommendationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        service_id = self.kwargs['service_id']
        return ServiceRecommendation.objects.filter(
            source_service_id=service_id,
            is_active=True
        ).order_by('-similarity_score')[:5]


class ProviderSentimentView(generics.RetrieveAPIView):
    """
    Get sentiment summary for a provider.
    """
    serializer_class = ProviderSentimentSummarySerializer
    permission_classes = [AllowAny]
    lookup_field = 'provider_id'

    def get_queryset(self):
        return ProviderSentimentSummary.objects.filter(is_active=True)

    def get_object(self):
        try:
            return super().get_object()
        except Exception:
            # Return empty sentiment data if none exists yet
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                provider = User.objects.get(id=self.kwargs.get('provider_id'))
                from django.utils import timezone
                from datetime import timedelta
                return ProviderSentimentSummary(
                    provider=provider,
                    period_start=timezone.now() - timedelta(days=90),
                    period_end=timezone.now(),
                    positive_count=0,
                    neutral_count=0,
                    negative_count=0,
                    total_reviews=0
                )
            except User.DoesNotExist:
                from django.http import Http404
                raise Http404