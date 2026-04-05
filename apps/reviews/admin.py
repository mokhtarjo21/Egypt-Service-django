"""
Admin configuration for reviews app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Review, ReviewHelpfulness


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for Review model.
    """
    list_display = ('service', 'reviewer', 'rating', 'status', 'created_at', 'helpful_count')
    list_filter = ('status', 'rating', 'created_at')
    search_fields = ('service__title_ar', 'reviewer__first_name', 'reviewer__last_name', 'title', 'comment')
    raw_id_fields = ('service', 'reviewer')
    actions = ['approve_reviews', 'reject_reviews']
    
    fieldsets = (
        (_('Review Details'), {
            'fields': ('service', 'reviewer', 'rating', 'title', 'comment')
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
        (_('Provider Response'), {
            'fields': ('provider_response', 'responded_at')
        }),
        (_('Helpfulness'), {
            'fields': ('helpful_count', 'unhelpful_count')
        }),
    )

    def approve_reviews(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f'{queryset.count()} reviews approved.')
    approve_reviews.short_description = 'Approve selected reviews'

    def reject_reviews(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f'{queryset.count()} reviews rejected.')
    reject_reviews.short_description = 'Reject selected reviews'


@admin.register(ReviewHelpfulness)
class ReviewHelpfulnessAdmin(admin.ModelAdmin):
    """
    Admin interface for ReviewHelpfulness model.
    """
    list_display = ('review', 'voter', 'vote', 'created_at')
    list_filter = ('vote', 'created_at')
    search_fields = ('review__service__title_ar', 'voter__first_name', 'voter__last_name')
    raw_id_fields = ('review', 'voter')