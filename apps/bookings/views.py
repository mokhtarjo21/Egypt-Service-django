"""
Booking views for Egyptian Service Marketplace.
Complete booking system implementation.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.notifications.utils import send_notification_if_enabled

from .models import Booking
from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    BookingCreateSerializer,
    BookingUpdateSerializer,
    BookingStatusUpdateSerializer,
    BookingCancelSerializer
)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bookings.
    
    Endpoints:
    - GET /api/v1/bookings/ - List all bookings (for current user)
    - POST /api/v1/bookings/ - Create a new booking
    - GET /api/v1/bookings/{id}/ - Get booking details
    - PATCH /api/v1/bookings/{id}/ - Update booking
    - DELETE /api/v1/bookings/{id}/ - Delete booking (admin only)
    - POST /api/v1/bookings/{id}/confirm/ - Confirm booking (provider)
    - POST /api/v1/bookings/{id}/start/ - Start service (provider)
    - POST /api/v1/bookings/{id}/complete/ - Complete booking (provider)
    - POST /api/v1/bookings/{id}/cancel/ - Cancel booking
    """
    
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_paid']
    search_fields = ['booking_number', 'service__title_ar', 'service__title_en']
    ordering_fields = ['created_at', 'scheduled_date', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get bookings for current user (as customer or provider)."""
        user = self.request.user
        
        # Admins can see all bookings
        if user.is_staff:
            return Booking.objects.select_related(
                'customer', 'provider', 'service'
            ).all()
        
        # Regular users see bookings they made or received
        return Booking.objects.select_related(
            'customer', 'provider', 'service'
        ).filter(
            Q(customer=user) | Q(provider=user)
        )
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return BookingListSerializer
        elif self.action == 'create':
            return BookingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BookingUpdateSerializer
        elif self.action == 'cancel':
            return BookingCancelSerializer
        return BookingDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new booking."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        
        # Notify provider
        send_notification_if_enabled(
            recipient=booking.provider,
            notification_type='booking',
            title_ar='حجز جديد',
            title_en='New Booking',
            message_ar=f'تلقيت طلب حجز جديد لخدمة "{booking.service.title_ar}" من {booking.customer.full_name}.',
            message_en=f'You received a new booking request for "{booking.service.title_en}" from {booking.customer.full_name}.',
            related_object=booking
        )
        
        # Return detailed booking info
        detail_serializer = BookingDetailSerializer(booking)
        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update booking (only certain fields and only if pending)."""
        booking = self.get_object()
        
        # Only customer can update, only if pending
        if booking.customer != request.user:
            return Response(
                {'error': _('You can only update your own bookings.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'pending':
            return Response(
                {'error': _('Only pending bookings can be updated.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a booking (provider only)."""
        booking = self.get_object()
        
        # Only provider can confirm
        if booking.provider != request.user:
            return Response(
                {'error': _('Only the service provider can confirm bookings.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            booking.confirm()
            # Notify customer
            send_notification_if_enabled(
                recipient=booking.customer,
                notification_type='booking',
                title_ar='تم تأكيد الحجز',
                title_en='Booking Confirmed',
                message_ar=f'تم تأكيد حجزك لخدمة "{booking.service.title_ar}" من قبل المزود.',
                message_en=f'Your booking for "{booking.service.title_en}" has been confirmed by the provider.',
                related_object=booking
            )
            return Response(
                BookingDetailSerializer(booking).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start service (provider only)."""
        booking = self.get_object()
        
        # Only provider can start
        if booking.provider != request.user:
            return Response(
                {'error': _('Only the service provider can start the service.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            booking.start_service()
            # Notify customer
            send_notification_if_enabled(
                recipient=booking.customer,
                notification_type='booking',
                title_ar='تم بدء الخدمة',
                title_en='Service Started',
                message_ar=f'بدأ المزود في تنفيذ خدمة "{booking.service.title_ar}".',
                message_en=f'The provider has started working on "{booking.service.title_en}".',
                related_object=booking
            )
            return Response(
                BookingDetailSerializer(booking).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a booking (provider only)."""
        booking = self.get_object()
        
        # Only provider can complete
        if booking.provider != request.user:
            return Response(
                {'error': _('Only the service provider can complete bookings.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            booking.complete()
            # Notify customer
            send_notification_if_enabled(
                recipient=booking.customer,
                notification_type='booking',
                title_ar='تم الانتهاء من الخدمة',
                title_en='Service Completed',
                message_ar=f'أنهى المزود خدمة "{booking.service.title_ar}". يرجى مراجعة الخدمة.',
                message_en=f'The provider has completed "{booking.service.title_en}". Please review it.',
                related_object=booking
            )
            return Response(
                BookingDetailSerializer(booking).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking."""
        booking = self.get_object()
        serializer = BookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user can cancel
        if booking.customer != request.user and booking.provider != request.user:
            return Response(
                {'error': _('You cannot cancel this booking.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            booking.cancel(
                cancelled_by=request.user,
                reason=serializer.validated_data['reason'],
                notes=serializer.validated_data.get('notes', '')
            )
            
            # Notify the other party
            other_party = booking.provider if request.user == booking.customer else booking.customer
            send_notification_if_enabled(
                recipient=other_party,
                notification_type='booking',
                title_ar='تم إلغاء الحجز',
                title_en='Booking Cancelled',
                message_ar=f'تم إلغاء حجز خدمة "{booking.service.title_ar}" بواسطة {request.user.full_name}. السبب: {serializer.validated_data["reason"]}',
                message_en=f'Booking for "{booking.service.title_en}" was cancelled by {request.user.full_name}. Reason: {serializer.validated_data["reason"]}',
                related_object=booking
            )
            
            return Response(
                BookingDetailSerializer(booking).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """Get bookings made by current user (as customer)."""
        bookings = Booking.objects.filter(
            customer=request.user
        ).select_related('provider', 'service').order_by('-created_at')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = BookingListSerializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def received_bookings(self, request):
        """Get bookings received by current user (as provider)."""
        bookings = Booking.objects.filter(
            provider=request.user
        ).select_related('customer', 'service').order_by('-created_at')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = BookingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = BookingListSerializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get booking statistics for current user."""
        user = request.user
        
        # Customer stats
        customer_stats = {
            'total': Booking.objects.filter(customer=user).count(),
            'pending': Booking.objects.filter(customer=user, status='pending').count(),
            'confirmed': Booking.objects.filter(customer=user, status='confirmed').count(),
            'completed': Booking.objects.filter(customer=user, status='completed').count(),
            'cancelled': Booking.objects.filter(
                customer=user,
                status__startswith='cancelled'
            ).count(),
        }
        
        # Provider stats
        provider_stats = {
            'total': Booking.objects.filter(provider=user).count(),
            'pending': Booking.objects.filter(provider=user, status='pending').count(),
            'confirmed': Booking.objects.filter(provider=user, status='confirmed').count(),
            'in_progress': Booking.objects.filter(provider=user, status='in_progress').count(),
            'completed': Booking.objects.filter(provider=user, status='completed').count(),
        }
        
        return Response({
            'customer': customer_stats,
            'provider': provider_stats
        })