from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ServiceRecommendation, ReviewSentiment, ProviderSentimentSummary


@admin.register(ServiceRecommendation)
class ServiceRecommendationAdmin(admin.ModelAdmin):
    list_display = (
        'source_service',
        'recommended_service',
        'similarity_score',
        'algorithm_version',
        'created_at',
        'updated_at',
    )
    list_filter = ('algorithm_version',)
    search_fields = (
        'source_service__title_ar',
        'recommended_service__title_ar',
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-similarity_score',)


@admin.register(ReviewSentiment)
class ReviewSentimentAdmin(admin.ModelAdmin):
    list_display = (
        'review',
        'sentiment',
        'confidence_score',
        'language_detected',
        'model_version',
        'created_at',
        'updated_at',
    )
    list_filter = ('sentiment', 'language_detected', 'model_version')
    search_fields = ('review__content', 'review__user__full_name', 'review__service__title_ar')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-confidence_score',)


@admin.register(ProviderSentimentSummary)
class ProviderSentimentSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'provider',
        'period_start',
        'period_end',
        'total_reviews',
        'positive_count',
        'neutral_count',
        'negative_count',
        'positive_percentage',
    )
    list_filter = ('period_start', 'period_end',)
    search_fields = ('provider__full_name',)
    readonly_fields = (
        'created_at', 'updated_at', 'positive_percentage'
    )
    ordering = ('-period_end',)

    def positive_percentage(self, obj):
        return f"{obj.positive_percentage:.2f}%"
    positive_percentage.short_description = _('Positive %')
