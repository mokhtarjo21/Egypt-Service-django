"""
Filters for the services app.
"""

import django_filters
from .models import Service, ServiceCategory, ServiceSubcategory


class ServiceFilter(django_filters.FilterSet):
    """
    Filter set for Service model.
    """
    category = django_filters.ModelChoiceFilter(
        queryset=ServiceCategory.objects.all(),
        to_field_name='slug'
    )
    subcategory = django_filters.ModelChoiceFilter(
        queryset=ServiceSubcategory.objects.all(),
        to_field_name='slug'
    )
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    pricing_type = django_filters.ChoiceFilter(choices=Service.PRICING_TYPE_CHOICES)
    governorate = django_filters.CharFilter(field_name='governorate__name_ar', lookup_expr='icontains')
    center = django_filters.CharFilter(field_name='center__name_ar', lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=Service.STATUS_CHOICES)
    
    class Meta:
        model = Service
        fields = ['category', 'subcategory', 'pricing_type', 'governorate', 'center', 'status']