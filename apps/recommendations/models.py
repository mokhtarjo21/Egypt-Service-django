"""
Recommendation and sentiment analysis models.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.services.models import Service
from apps.reviews.models import Review

User = get_user_model()


class ServiceRecommendation(BaseModel):
    """
    Service recommendations based on ML algorithms.
    """
    source_service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='recommendations_from'
    )
    recommended_service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='recommendations_to'
    )
    similarity_score = models.FloatField(_('Similarity score'))
    algorithm_version = models.CharField(_('Algorithm version'), max_length=20)
    factors = models.JSONField(_('Recommendation factors'), default=dict)
    
    class Meta:
        verbose_name = _('Service Recommendation')
        verbose_name_plural = _('Service Recommendations')
        unique_together = ['source_service', 'recommended_service']
        ordering = ['-similarity_score']

    def __str__(self):
        return f"{self.source_service.title_ar} → {self.recommended_service.title_ar}"


class ReviewSentiment(BaseModel):
    """
    Sentiment analysis results for reviews.
    """
    SENTIMENT_CHOICES = [
        ('positive', _('Positive')),
        ('neutral', _('Neutral')),
        ('negative', _('Negative')),
    ]

    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,
        related_name='sentiment'
    )
    sentiment = models.CharField(
        _('Sentiment'),
        max_length=10,
        choices=SENTIMENT_CHOICES
    )
    confidence_score = models.FloatField(_('Confidence score'))
    aspects = models.JSONField(_('Aspect analysis'), default=dict)
    language_detected = models.CharField(_('Language'), max_length=2)
    model_version = models.CharField(_('Model version'), max_length=20)
    
    class Meta:
        verbose_name = _('Review Sentiment')
        verbose_name_plural = _('Review Sentiments')

    def __str__(self):
        return f"{self.review.id} - {self.sentiment} ({self.confidence_score:.2f})"


class ProviderSentimentSummary(BaseModel):
    """
    90-day sentiment summary for providers.
    """
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sentiment_summaries'
    )
    period_start = models.DateTimeField(_('Period start'))
    period_end = models.DateTimeField(_('Period end'))
    
    # Sentiment counts
    positive_count = models.PositiveIntegerField(_('Positive reviews'), default=0)
    neutral_count = models.PositiveIntegerField(_('Neutral reviews'), default=0)
    negative_count = models.PositiveIntegerField(_('Negative reviews'), default=0)
    total_reviews = models.PositiveIntegerField(_('Total reviews'), default=0)
    
    # Aspect scores (0-100)
    punctuality_score = models.FloatField(_('Punctuality score'), default=0)
    quality_score = models.FloatField(_('Quality score'), default=0)
    communication_score = models.FloatField(_('Communication score'), default=0)
    value_score = models.FloatField(_('Value for money score'), default=0)
    
    class Meta:
        verbose_name = _('Provider Sentiment Summary')
        verbose_name_plural = _('Provider Sentiment Summaries')
        unique_together = ['provider', 'period_start', 'period_end']
        ordering = ['-period_end']

    def __str__(self):
        return f"{self.provider.full_name} - {self.period_start.date()}"

    @property
    def positive_percentage(self):
        if self.total_reviews == 0:
            return 0
        return (self.positive_count / self.total_reviews) * 100