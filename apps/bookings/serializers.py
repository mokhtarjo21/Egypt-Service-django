"""
Booking serializers for Egyptian Service Marketplace.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Booking
from apps.services.serializers import ServiceSerializer
from apps.accounts.serializers import UserSerializer


class BookingListSerializer(serializers.ModelSerializer):
    """Serializer for listing bookings."""
    
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    provider_name = serializers.CharField(source='provider.full_name', read_only=True)
    service_title = serializers.CharField(source='service.title_ar', read_only=True)
    service_title_en = serializers.CharField(source='service.title_en', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    image = serializers.CharField(source='service.primary_image.image', read_only=True)
    class Meta:
        model = Booking
        fields = [
            'id', 'image','booking_number', 'customer_name', 'provider_name',
            'service_title', 'service_title_en', 'status', 'status_display',
            'scheduled_date', 'scheduled_end_date', 'total_amount',
            'is_paid', 'created_at', 'is_active'
        ]
        read_only_fields = ['booking_number', 'created_at']


class BookingDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for booking information."""
    
    customer = UserSerializer(read_only=True)
    provider = UserSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_cancel = serializers.SerializerMethodField()
    can_review = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_number', 'customer', 'provider', 'service',
            'status', 'status_display', 'scheduled_date', 'scheduled_end_date',
            'completed_at', 'service_price', 'additional_charges', 'discount',
            'total_amount', 'customer_notes', 'provider_notes',
            'location_address', 'location_governorate', 'location_city',
            'is_paid', 'payment_method', 'cancelled_at', 'cancellation_reason',
            'cancellation_notes', 'is_refunded', 'refund_amount',
            'created_at', 'updated_at', 'can_cancel', 'can_review', 'is_active'
        ]
        read_only_fields = [
            'booking_number', 'customer', 'provider', 'service',
            'completed_at', 'cancelled_at', 'is_refunded', 'refund_amount',
            'created_at', 'updated_at'
        ]
    
    def get_can_cancel(self, obj):
        """Check if booking can be cancelled."""
        return obj.can_be_cancelled()


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new booking."""
    
    service_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'service_id', 'scheduled_date', 'scheduled_end_date',
            'customer_notes', 'location_address', 'location_governorate',
            'location_city', 'service_price', 'additional_charges', 'discount'
        ]
    
    def validate_scheduled_date(self, value):
        """Validate that scheduled date is in the future."""
        if value <= timezone.now():
            raise serializers.ValidationError(
                _('Scheduled date must be in the future.')
            )
        return value
    
    def validate(self, attrs):
        """Validate booking data."""
        scheduled_date = attrs.get('scheduled_date')
        scheduled_end_date = attrs.get('scheduled_end_date')
        
        if scheduled_end_date and scheduled_end_date <= scheduled_date:
            raise serializers.ValidationError({
                'scheduled_end_date': _('End date must be after start date.')
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create a new booking."""
        from apps.services.models import Service
        
        service_id = validated_data.pop('service_id')
        service = Service.objects.get(id=service_id)
        
        # Set customer from request
        customer = self.context['request'].user
        
        # Create booking
        booking = Booking.objects.create(
            customer=customer,
            service=service,
            provider=service.owner,
            **validated_data
        )
        
        return booking


class BookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating booking information."""
    
    class Meta:
        model = Booking
        fields = [
            'scheduled_date', 'scheduled_end_date', 'customer_notes',
            'location_address', 'location_governorate', 'location_city'
        ]
    
    def validate_scheduled_date(self, value):
        """Validate that scheduled date is in the future."""
        if value <= timezone.now():
            raise serializers.ValidationError(
                _('Scheduled date must be in the future.')
            )
        return value


class BookingStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating booking status."""
    
    action = serializers.ChoiceField(
        choices=['confirm', 'start', 'complete', 'cancel']
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    cancellation_reason = serializers.ChoiceField(
        choices=Booking.CANCELLATION_REASON_CHOICES,
        required=False
    )
    
    def validate(self, attrs):
        """Validate status update."""
        action = attrs.get('action')
        
        if action == 'cancel':
            if 'cancellation_reason' not in attrs:
                raise serializers.ValidationError({
                    'cancellation_reason': _('Cancellation reason is required.')
                })
        
        return attrs


class BookingCancelSerializer(serializers.Serializer):
    """Serializer for cancelling a booking."""
    
    reason = serializers.ChoiceField(choices=Booking.CANCELLATION_REASON_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)