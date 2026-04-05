"""
Review models for Egyptian Service Marketplace.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import BaseModel
from apps.services.models import Service

User = get_user_model()


class Review(BaseModel):
    """
    Reviews for services.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    rating = models.PositiveIntegerField(
        _('Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(_('Title'), max_length=200)
    comment = models.TextField(_('Comment'))
    status = models.CharField(
        _('Status'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Response from service provider
    provider_response = models.TextField(_('Provider response'), blank=True)
    responded_at = models.DateTimeField(_('Responded at'), null=True, blank=True)
    
    # Helpfulness ratings
    helpful_count = models.PositiveIntegerField(_('Helpful count'), default=0)
    unhelpful_count = models.PositiveIntegerField(_('Unhelpful count'), default=0)

    class Meta:
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')
        ordering = ['-created_at']
        unique_together = ['service', 'reviewer']  # One review per service per user

    def __str__(self):
        return f"{self.reviewer.full_name} - {self.service.title_ar} ({self.rating}/5)"

    @property
    def helpfulness_ratio(self):
        total = self.helpful_count + self.unhelpful_count
        if total == 0:
            return 0
        return (self.helpful_count / total) * 100
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update service and provider ratings
        if self.status == 'approved':
            self.update_ratings()
    
    def update_ratings(self):
        """Update service and provider average ratings."""
        from django.db.models import Avg
        
        # Update service rating
        service_avg = Review.objects.filter(
            service=self.service,
            status='approved'
        ).aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        if service_avg:
            # Update service rating (if service model has rating field)
            pass
        
        # Update provider profile rating
        provider_avg = Review.objects.filter(
            service__owner=self.service.owner,
            status='approved'
        ).aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        if provider_avg:
            profile, created = self.service.owner.profile.get_or_create()
            profile.rating = provider_avg
            profile.total_reviews = Review.objects.filter(
                service__owner=self.service.owner,
                status='approved'
            ).count()
            profile.save()


class ReviewHelpfulness(BaseModel):
    """
    Track which users found reviews helpful or not.
    """
    VOTE_CHOICES = [
        ('helpful', _('Helpful')),
        ('unhelpful', _('Not Helpful')),
    ]

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpfulness_votes'
    )
    voter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='review_votes'
    )
    vote = models.CharField(
        _('Vote'),
        max_length=10,
        choices=VOTE_CHOICES
    )

    class Meta:
        verbose_name = _('Review Helpfulness')
        verbose_name_plural = _('Review Helpfulness')
        unique_together = ['review', 'voter']  # One vote per review per user

    def __str__(self):
        return f"{self.voter.full_name} - {self.get_vote_display()}"