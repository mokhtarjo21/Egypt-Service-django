"""
Serializers for the subscriptions app.
"""

from rest_framework import serializers
from .models import SubscriptionPlan, Subscription, Invoice, AddonCredit, Coupon, SubscriptionUsage, BillingAddress


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for SubscriptionPlan model.
    """
    monthly_price = serializers.ReadOnlyField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name_ar', 'name_en', 'plan_type', 'billing_period',
            'price', 'monthly_price', 'currency', 'max_services', 'max_team_members',
            'has_advanced_analytics', 'has_priority_support', 'search_ranking_boost',
            'featured_credits_included', 'description_ar', 'description_en',
            'features_ar', 'features_en', 'is_popular'
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for Subscription model.
    """
    plan = SubscriptionPlanSerializer(read_only=True)
    days_until_renewal = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'status', 'current_period_start', 'current_period_end',
            'trial_start', 'trial_end', 'canceled_at', 'services_count',
            'team_members_count', 'featured_credits_used', 'days_until_renewal',
            'is_active', 'created_at'
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    """
    Serializer for Invoice model.
    """
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'status', 'subtotal', 'tax_amount',
            'total_amount', 'currency', 'period_start', 'period_end',
            'due_date', 'paid_at', 'pdf_file', 'created_at'
        ]


class AddonCreditSerializer(serializers.ModelSerializer):
    """
    Serializer for AddonCredit model.
    """
    remaining_credits = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = AddonCredit
        fields = [
            'id', 'credit_type', 'amount', 'used_amount', 'remaining_credits',
            'expires_at', 'is_expired', 'purchase_price', 'currency', 'created_at'
        ]


class CouponSerializer(serializers.ModelSerializer):
    """
    Serializer for Coupon model.
    """
    is_valid = serializers.ReadOnlyField()
    
    class Meta:
        model = Coupon
        fields = [
            'code', 'name_ar', 'name_en', 'discount_type', 'discount_value',
            'max_discount_amount', 'valid_from', 'valid_until', 'max_uses',
            'used_count', 'first_time_only', 'minimum_amount', 'is_valid'
        ]


class SubscriptionUsageSerializer(serializers.ModelSerializer):
    """
    Serializer for SubscriptionUsage model.
    """
    limits_check = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionUsage
        fields = [
            'services_count', 'team_members_count', 'featured_credits_used',
            'storage_used_mb', 'monthly_api_calls', 'monthly_messages_sent',
            'last_reset_at', 'limits_check'
        ]
    
    def get_limits_check(self, obj):
        return obj.check_limits()


class BillingAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for BillingAddress model.
    """
    class Meta:
        model = BillingAddress
        fields = [
            'id', 'company_name', 'address_line_1', 'address_line_2',
            'city', 'governorate', 'postal_code', 'country', 'tax_id',
            'is_default'
        ]


class SubscriptionCreateSerializer(serializers.Serializer):
    """
    Serializer for creating subscriptions.
    """
    plan_id = serializers.UUIDField()
    payment_method_id = serializers.CharField(max_length=100)
    coupon_code = serializers.CharField(max_length=50, required=False)
    billing_address = BillingAddressSerializer(required=False)


class CouponValidationSerializer(serializers.Serializer):
    """
    Serializer for validating coupons.
    """
    code = serializers.CharField(max_length=50)
    plan_id = serializers.UUIDField()