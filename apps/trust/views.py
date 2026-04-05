"""
Views for the trust app.
"""

from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Badge, UserBadge, TrustMetric
from .serializers import BadgeSerializer, UserBadgeSerializer, TrustMetricSerializer


class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for badges.
    """
    queryset = Badge.objects.filter(is_active=True)
    serializer_class = BadgeSerializer
    permission_classes = [AllowAny]


class UserBadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user badges.
    """
    serializer_class = UserBadgeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserBadge.objects.filter(
            user=self.request.user,
            is_active=True
        )


class TrustMetricsView(generics.ListAPIView):
    """
    View for user trust metrics.
    """
    serializer_class = TrustMetricSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return TrustMetric.objects.filter(
            user_id=user_id,
            is_active=True
        ).order_by('-calculation_date')[:10]