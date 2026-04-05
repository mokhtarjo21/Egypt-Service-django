"""
Views for the analytics app.
"""

from datetime import datetime, timedelta
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
import csv

from .models import EventTracking, ProviderAnalytics, PlatformAnalytics, GovernorateAnalytics
from .serializers import (
    EventTrackingSerializer,
    ProviderAnalyticsSerializer,
    PlatformAnalyticsSerializer,
    GovernorateAnalyticsSerializer
)
from apps.accounts.models import User
from apps.services.models import Service
from apps.reviews.models import Review


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_event(request):
    """
    Track user events for analytics.
    """
    serializer = EventTrackingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_id=request.session.session_key or ''
        )
        return Response({'status': 'tracked'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProviderAnalyticsView(generics.ListAPIView):
    """
    Provider analytics dashboard.
    """
    serializer_class = ProviderAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        days = int(self.request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        return ProviderAnalytics.objects.filter(
            provider=user,
            date__gte=start_date
        ).order_by('-date')

    def get(self, request, *args, **kwargs):
        # Get aggregated data
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Current period data
        current_analytics = self.get_queryset()
        
        # Previous period for comparison
        previous_start = start_date - timedelta(days=days)
        previous_analytics = ProviderAnalytics.objects.filter(
            provider=request.user,
            date__gte=previous_start,
            date__lt=start_date
        )
        
        # Aggregate current period
        current_totals = current_analytics.aggregate(
            total_profile_views=Sum('profile_views'),
            total_service_views=Sum('service_views'),
            total_service_clicks=Sum('service_clicks'),
            total_messages=Sum('messages_received'),
            total_bookings=Sum('bookings_count'),
            total_revenue=Sum('revenue'),
            avg_rating=Avg('average_rating'),
            avg_response_time=Avg('response_time_minutes'),
        )
        
        # Aggregate previous period
        previous_totals = previous_analytics.aggregate(
            total_profile_views=Sum('profile_views'),
            total_service_views=Sum('service_views'),
            total_service_clicks=Sum('service_clicks'),
            total_messages=Sum('messages_received'),
            total_bookings=Sum('bookings_count'),
            total_revenue=Sum('revenue'),
        )
        
        # Calculate conversion rate
        total_views = current_totals['total_service_views'] or 0
        total_inquiries = current_totals['total_messages'] or 0
        conversion_rate = (total_inquiries / total_views * 100) if total_views > 0 else 0
        
        # Top performing services
        top_services = Service.objects.filter(
            owner=request.user,
            is_active=True
        ).annotate(
            total_views=Count('events', filter=Q(events__event_type='service_view'))
        ).order_by('-total_views')[:5]

        
        # Regional performance
        regional_data = EventTracking.objects.filter(
            user=request.user,
            event_type='service_view',
            created_at__date__gte=start_date,
            governorate__isnull=False
        ).values('governorate__name_ar').annotate(
            views=Count('id')
        ).order_by('-views')[:10]
        
        return Response({
            'period_days': days,
            'current_totals': current_totals,
            'previous_totals': previous_totals,
            'conversion_rate': conversion_rate,
            'daily_data': self.get_serializer(current_analytics, many=True).data,
            'top_services': [
                {
                    'title': service.title_ar,
                    'views': service.total_views,
                    'slug': service.slug
                }
                for service in top_services
            ],
            'regional_performance': list(regional_data),
        })


class AdminAnalyticsView(generics.GenericAPIView):
    """
    Admin analytics dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.role == 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Platform metrics
        platform_data = PlatformAnalytics.objects.filter(
            date__gte=start_date
        ).order_by('-date')
        
        # User metrics
        user_stats = User.objects.aggregate(
            total_users=Count('id'),
            verified_users=Count('id', filter=Q(status='verified')),
            pending_users=Count('id', filter=Q(status='pending')),
            new_users_today=Count('id', filter=Q(date_joined__date=timezone.now().date())),
        )
        
        # Service metrics
        service_stats = Service.objects.aggregate(
            total_services=Count('id'),
            approved_services=Count('id', filter=Q(status='approved')),
            pending_services=Count('id', filter=Q(status='pending')),
            new_services_today=Count('id', filter=Q(created_at__date=timezone.now().date())),
        )
        
        # Governorate breakdown
        governorate_data = GovernorateAnalytics.objects.filter(
            date__gte=start_date
        ).values('governorate__name_ar').annotate(
            total_services=Sum('services_count'),
            total_bookings=Sum('bookings_count'),
            total_revenue=Sum('revenue')
        ).order_by('-total_services')[:10]
        
        # User cohort retention (simplified)
        cohort_data = []
        for i in range(12):  # Last 12 months
            month_start = timezone.now().date().replace(day=1) - timedelta(days=30*i)
            month_users = User.objects.filter(
                date_joined__date__gte=month_start,
                date_joined__date__lt=month_start + timedelta(days=30)
            ).count()
            
            # Active users from that cohort in current month
            active_users = User.objects.filter(
                date_joined__date__gte=month_start,
                date_joined__date__lt=month_start + timedelta(days=30),
                last_login__date__gte=timezone.now().date() - timedelta(days=30)
            ).count()
            
            retention_rate = (active_users / month_users * 100) if month_users > 0 else 0
            
            cohort_data.append({
                'month': month_start.strftime('%Y-%m'),
                'new_users': month_users,
                'active_users': active_users,
                'retention_rate': retention_rate
            })
        
        return Response({
            'user_stats': user_stats,
            'service_stats': service_stats,
            'daily_platform_data': PlatformAnalyticsSerializer(platform_data, many=True).data,
            'governorate_breakdown': list(governorate_data),
            'cohort_retention': cohort_data[:6],  # Last 6 months
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_analytics_csv(request):
    """
    Export analytics data as CSV.
    """
    if not request.user.role == 'admin':
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    days = int(request.query_params.get('days', 30))
    start_date = timezone.now().date() - timedelta(days=days)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="analytics_{start_date}_to_{timezone.now().date()}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Total Users', 'New Users', 'Active Users', 'Total Services',
        'New Services', 'Approved Services', 'Page Views', 'Service Views',
        'Total Revenue', 'Commission Revenue'
    ])
    
    analytics = PlatformAnalytics.objects.filter(date__gte=start_date).order_by('date')
    for record in analytics:
        writer.writerow([
            record.date,
            record.total_users,
            record.new_users,
            record.active_users,
            record.total_services,
            record.new_services,
            record.approved_services,
            record.page_views,
            record.service_views,
            record.total_revenue,
            record.commission_revenue,
        ])
    
    return response