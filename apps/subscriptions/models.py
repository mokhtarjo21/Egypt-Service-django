"""
Subscription and billing models for Egyptian Service Marketplace.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from apps.core.models import BaseModel

User = get_user_model()


class SubscriptionPlan(BaseModel):
    """
    Subscription plans available on the platform.
    """
    PLAN_TYPE_CHOICES = [
        ('free', _('Free')),
        ('pro', _('Pro')),
        ('business', _('Business')),
    ]
    
    BILLING_PERIOD_CHOICES = [
        ('monthly', _('Monthly')),
        ('annual', _('Annual')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name_ar = models.CharField(_('Arabic name'), max_length=100)
    name_en = models.CharField(_('English name'), max_length=100)
    plan_type = models.CharField(_('Plan type'), max_length=10, choices=PLAN_TYPE_CHOICES)
    billing_period = models.CharField(_('Billing period'), max_length=10, choices=BILLING_PERIOD_CHOICES)
    
    # Pricing
    price = models.DecimalField(_('Price'), max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(_('Currency'), max_length=3, default='EGP')
    
    # Features & Limits
    max_services = models.PositiveIntegerField(_('Max services'), default=3)
    max_team_members = models.PositiveIntegerField(_('Max team members'), default=1)
    has_advanced_analytics = models.BooleanField(_('Advanced analytics'), default=False)
    has_priority_support = models.BooleanField(_('Priority support'), default=False)
    search_ranking_boost = models.FloatField(_('Search ranking boost'), default=1.0)
    featured_credits_included = models.PositiveIntegerField(_('Featured credits'), default=0)
    
    # Stripe integration
    stripe_price_id = models.CharField(_('Stripe price ID'), max_length=100, blank=True)
    
    # Display
    description_ar = models.TextField(_('Arabic description'), blank=True)
    description_en = models.TextField(_('English description'), blank=True)
    features_ar = models.JSONField(_('Arabic features'), default=list)
    features_en = models.JSONField(_('English features'), default=list)
    is_popular = models.BooleanField(_('Popular plan'), default=False)
    sort_order = models.PositiveIntegerField(_('Sort order'), default=0)

    class Meta:
        verbose_name = _('Subscription Plan')
        verbose_name_plural = _('Subscription Plans')
        ordering = ['sort_order', 'price']
        unique_together = ['plan_type', 'billing_period']

    def __str__(self):
        return f"{self.name_ar} ({self.get_billing_period_display()})"

    @property
    def monthly_price(self):
        """Calculate monthly equivalent price."""
        if self.billing_period == 'annual':
            return self.price / 12
        return self.price


class Subscription(BaseModel):
    """
    User subscriptions.
    """
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('past_due', _('Past Due')),
        ('canceled', _('Canceled')),
        ('unpaid', _('Unpaid')),
        ('incomplete', _('Incomplete')),
        ('trialing', _('Trialing')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES)
    
    # Billing
    current_period_start = models.DateTimeField(_('Current period start'))
    current_period_end = models.DateTimeField(_('Current period end'))
    trial_start = models.DateTimeField(_('Trial start'), null=True, blank=True)
    trial_end = models.DateTimeField(_('Trial end'), null=True, blank=True)
    canceled_at = models.DateTimeField(_('Canceled at'), null=True, blank=True)
    
    # Stripe integration
    stripe_subscription_id = models.CharField(_('Stripe subscription ID'), max_length=100, blank=True)
    stripe_customer_id = models.CharField(_('Stripe customer ID'), max_length=100, blank=True)
    
    # Paymob integration
    paymob_order_id = models.CharField(_('Paymob Order ID'), max_length=100, blank=True)
    
    # Usage tracking
    services_count = models.PositiveIntegerField(_('Services count'), default=0)
    team_members_count = models.PositiveIntegerField(_('Team members count'), default=1)
    featured_credits_used = models.PositiveIntegerField(_('Featured credits used'), default=0)

    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.plan.name_ar}"

    @property
    def is_active(self):
        return self.status == 'active' and timezone.now() < self.current_period_end

    @property
    def days_until_renewal(self):
        if self.current_period_end:
            delta = self.current_period_end - timezone.now()
            return max(0, delta.days)
        return 0

    def can_create_service(self):
        """Check if user can create a new service based on plan limits."""
        return self.services_count < self.plan.max_services

    def can_add_team_member(self):
        """Check if user can add a new team member."""
        return self.team_members_count < self.plan.max_team_members

    def has_featured_credits(self):
        """Check if user has remaining featured credits."""
        total_credits = self.plan.featured_credits_included + self.addon_credits.filter(
            credit_type='featured',
            expires_at__gt=timezone.now()
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        return total_credits > self.featured_credits_used


class Invoice(BaseModel):
    """
    Billing invoices.
    """
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('open', _('Open')),
        ('paid', _('Paid')),
        ('void', _('Void')),
        ('uncollectible', _('Uncollectible')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    invoice_number = models.CharField(_('Invoice number'), max_length=50, unique=True)
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES)
    
    # Amounts
    subtotal = models.DecimalField(_('Subtotal'), max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(_('Tax amount'), max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(_('Total amount'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='EGP')
    
    # Dates
    period_start = models.DateTimeField(_('Period start'))
    period_end = models.DateTimeField(_('Period end'))
    due_date = models.DateTimeField(_('Due date'))
    paid_at = models.DateTimeField(_('Paid at'), null=True, blank=True)
    
    # Stripe integration
    stripe_invoice_id = models.CharField(_('Stripe invoice ID'), max_length=100, blank=True)
    stripe_payment_intent_id = models.CharField(_('Stripe payment intent ID'), max_length=100, blank=True)
    
    # Files
    pdf_file = models.FileField(_('PDF invoice'), upload_to='invoices/', null=True, blank=True)

    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.subscription.user.full_name}"

    def generate_invoice_number(self):
        """Generate unique invoice number."""
        from datetime import datetime
        year = datetime.now().year
        month = datetime.now().month
        count = Invoice.objects.filter(created_at__year=year, created_at__month=month).count() + 1
        return f"INV-{year}{month:02d}-{count:04d}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)


class AddonCredit(BaseModel):
    """
    Add-on credits for featured placements, etc.
    """
    CREDIT_TYPE_CHOICES = [
        ('featured', _('Featured Placement')),
        ('boost', _('Search Boost')),
        ('analytics', _('Advanced Analytics')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='addon_credits'
    )
    credit_type = models.CharField(_('Credit type'), max_length=15, choices=CREDIT_TYPE_CHOICES)
    amount = models.PositiveIntegerField(_('Credit amount'))
    used_amount = models.PositiveIntegerField(_('Used amount'), default=0)
    expires_at = models.DateTimeField(_('Expires at'))
    
    # Purchase details
    purchase_price = models.DecimalField(_('Purchase price'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='EGP')

    class Meta:
        verbose_name = _('Addon Credit')
        verbose_name_plural = _('Addon Credits')
        ordering = ['expires_at']

    def __str__(self):
        return f"{self.subscription.user.full_name} - {self.get_credit_type_display()} ({self.amount})"

    @property
    def remaining_credits(self):
        return self.amount - self.used_amount

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class FeatureFlag(BaseModel):
    """
    Feature flags for subscription-based features.
    """
    key = models.CharField(_('Feature key'), max_length=100, unique=True)
    name_ar = models.CharField(_('Arabic name'), max_length=100)
    name_en = models.CharField(_('English name'), max_length=100)
    description_ar = models.TextField(_('Arabic description'), blank=True)
    description_en = models.TextField(_('English description'), blank=True)
    
    # Plan requirements
    required_plan_types = models.JSONField(_('Required plan types'), default=list)
    is_global = models.BooleanField(_('Global feature'), default=False)
    
    class Meta:
        verbose_name = _('Feature Flag')
        verbose_name_plural = _('Feature Flags')
        ordering = ['key']

    def __str__(self):
        return self.name_ar

    def is_enabled_for_user(self, user):
        """Check if feature is enabled for a specific user."""
        if self.is_global:
            return True
        
        if not user.is_authenticated:
            return False
        
        # Check user's subscription
        subscription = user.subscriptions.filter(status='active').first()
        if not subscription:
            return 'free' in self.required_plan_types
        
        return subscription.plan.plan_type in self.required_plan_types


class UsageRecord(BaseModel):
    """
    Track usage for billing and analytics.
    """
    USAGE_TYPE_CHOICES = [
        ('service_created', _('Service Created')),
        ('featured_placement', _('Featured Placement')),
        ('team_member_added', _('Team Member Added')),
        ('api_call', _('API Call')),
        ('storage_used', _('Storage Used')),
    ]

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='usage_records'
    )
    usage_type = models.CharField(_('Usage type'), max_length=20, choices=USAGE_TYPE_CHOICES)
    quantity = models.PositiveIntegerField(_('Quantity'), default=1)
    timestamp = models.DateTimeField(_('Timestamp'), default=timezone.now)
    
    # Metadata
    metadata = models.JSONField(_('Metadata'), default=dict)
    
    # Billing
    unit_price = models.DecimalField(_('Unit price'), max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(_('Total amount'), max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _('Usage Record')
        verbose_name_plural = _('Usage Records')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['subscription', 'usage_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.subscription.user.full_name} - {self.get_usage_type_display()}"


class Coupon(BaseModel):
    """
    Discount coupons for subscriptions.
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', _('Percentage')),
        ('fixed', _('Fixed Amount')),
    ]

    code = models.CharField(_('Coupon code'), max_length=50, unique=True)
    name_ar = models.CharField(_('Arabic name'), max_length=100)
    name_en = models.CharField(_('English name'), max_length=100)
    
    # Discount
    discount_type = models.CharField(_('Discount type'), max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(_('Discount value'), max_digits=10, decimal_places=2)
    max_discount_amount = models.DecimalField(_('Max discount amount'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Validity
    valid_from = models.DateTimeField(_('Valid from'))
    valid_until = models.DateTimeField(_('Valid until'))
    max_uses = models.PositiveIntegerField(_('Max uses'), null=True, blank=True)
    used_count = models.PositiveIntegerField(_('Used count'), default=0)
    
    # Restrictions
    applicable_plans = models.ManyToManyField(SubscriptionPlan, blank=True)
    first_time_only = models.BooleanField(_('First time customers only'), default=False)
    minimum_amount = models.DecimalField(_('Minimum amount'), max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = _('Coupon')
        verbose_name_plural = _('Coupons')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.name_ar}"

    @property
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.max_uses is None or self.used_count < self.max_uses)
        )

    def calculate_discount(self, amount):
        """Calculate discount amount for given price."""
        if not self.is_valid:
            return Decimal('0')
        
        if self.discount_type == 'percentage':
            discount = amount * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:
            discount = min(self.discount_value, amount)
        
        return discount


class SubscriptionUsage(BaseModel):
    """
    Current usage tracking for subscriptions.
    """
    subscription = models.OneToOneField(
        Subscription,
        on_delete=models.CASCADE,
        related_name='current_usage'
    )
    
    # Current usage
    services_count = models.PositiveIntegerField(_('Services count'), default=0)
    team_members_count = models.PositiveIntegerField(_('Team members count'), default=1)
    featured_credits_used = models.PositiveIntegerField(_('Featured credits used'), default=0)
    storage_used_mb = models.PositiveIntegerField(_('Storage used (MB)'), default=0)
    
    # Monthly usage (resets each billing cycle)
    monthly_api_calls = models.PositiveIntegerField(_('Monthly API calls'), default=0)
    monthly_messages_sent = models.PositiveIntegerField(_('Monthly messages sent'), default=0)
    
    # Last reset
    last_reset_at = models.DateTimeField(_('Last reset at'), default=timezone.now)

    class Meta:
        verbose_name = _('Subscription Usage')
        verbose_name_plural = _('Subscription Usage')

    def __str__(self):
        return f"Usage for {self.subscription.user.full_name}"

    def reset_monthly_usage(self):
        """Reset monthly usage counters."""
        self.monthly_api_calls = 0
        self.monthly_messages_sent = 0
        self.last_reset_at = timezone.now()
        self.save()

    def check_limits(self):
        """Check if user is within plan limits."""
        plan = self.subscription.plan
        return {
            'services': self.services_count < plan.max_services,
            'team_members': self.team_members_count < plan.max_team_members,
            'featured_credits': self.subscription.has_featured_credits(),
        }


class BillingAddress(BaseModel):
    """
    Billing addresses for invoices.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='billing_addresses'
    )
    company_name = models.CharField(_('Company name'), max_length=200, blank=True)
    address_line_1 = models.CharField(_('Address line 1'), max_length=200)
    address_line_2 = models.CharField(_('Address line 2'), max_length=200, blank=True)
    city = models.CharField(_('City'), max_length=100)
    governorate = models.CharField(_('Governorate'), max_length=100)
    postal_code = models.CharField(_('Postal code'), max_length=20, blank=True)
    country = models.CharField(_('Country'), max_length=2, default='EG')
    
    # Tax information
    tax_id = models.CharField(_('Tax ID'), max_length=50, blank=True)
    is_default = models.BooleanField(_('Default address'), default=False)

    class Meta:
        verbose_name = _('Billing Address')
        verbose_name_plural = _('Billing Addresses')

    def __str__(self):
        return f"{self.user.full_name} - {self.city}, {self.governorate}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default address per user
            BillingAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)