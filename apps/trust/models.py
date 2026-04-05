"""
Trust and badge models for Egyptian Service Marketplace.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from apps.core.models import BaseModel
from apps.services.models import Service

User = get_user_model()


class Badge(BaseModel):
    """
    Badge definitions for trust signals.
    """
    BADGE_TYPE_CHOICES = [
        ('verified', _('Verified')),
        ('top_rated', _('Top Rated')),
        ('responsive', _('Responsive')),
        ('featured', _('Featured')),
        ('expert', _('Expert')),
        ('new_provider', _('New Provider')),
    ]

    name_ar = models.CharField(_('Arabic name'), max_length=100)
    name_en = models.CharField(_('English name'), max_length=100)
    badge_type = models.CharField(
        _('Badge type'),
        max_length=20,
        choices=BADGE_TYPE_CHOICES,
        unique=True
    )
    description_ar = models.TextField(_('Arabic description'))
    description_en = models.TextField(_('English description'))
    icon = models.CharField(_('Icon'), max_length=50)
    color = models.CharField(_('Color'), max_length=7, default='#3B82F6')
    criteria_config = models.JSONField(_('Criteria configuration'), default=dict)
    search_boost = models.FloatField(_('Search ranking boost'), default=1.0)
    is_active = models.BooleanField(_('Active'), default=True)
    
    class Meta:
        verbose_name = _('Badge')
        verbose_name_plural = _('Badges')
        ordering = ['badge_type']

    def __str__(self):
        return self.name_ar


class UserBadge(BaseModel):
    """
    Badge assignments to users with validity periods.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='badges'
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    earned_at = models.DateTimeField(_('Earned at'), default=timezone.now)
    expires_at = models.DateTimeField(_('Expires at'), null=True, blank=True)
    is_manual = models.BooleanField(_('Manual assignment'), default=False)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='badges_assigned'
    )
    notes = models.TextField(_('Admin notes'), blank=True)
    
    class Meta:
        verbose_name = _('User Badge')
        verbose_name_plural = _('User Badges')
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.badge.name_ar}"

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at:
            return timezone.now() < self.expires_at
        return True


class TrustMetric(BaseModel):
    """
    Trust metrics for badge calculation.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='trust_metrics'
    )
    metric_type = models.CharField(
        _('Metric type'),
        max_length=30,
        choices=[
            ('avg_rating', _('Average Rating')),
            ('total_reviews', _('Total Reviews')),
            ('response_time_minutes', _('Response Time (minutes)')),
            ('completion_rate', _('Completion Rate')),
            ('cancellation_rate', _('Cancellation Rate')),
            ('repeat_customer_rate', _('Repeat Customer Rate')),
        ]
    )
    value = models.FloatField(_('Value'))
    period_start = models.DateTimeField(_('Period start'))
    period_end = models.DateTimeField(_('Period end'))
    calculation_date = models.DateTimeField(_('Calculated at'), default=timezone.now)
    
    class Meta:
        verbose_name = _('Trust Metric')
        verbose_name_plural = _('Trust Metrics')
        unique_together = ['user', 'metric_type', 'period_start', 'period_end']
        ordering = ['-calculation_date']

    def __str__(self):
        return f"{self.user.full_name} - {self.metric_type}: {self.value}"