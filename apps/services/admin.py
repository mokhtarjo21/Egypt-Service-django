from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    ServiceCategory,
    ServiceSubcategory,
    Service,
    ServiceImage,
    ServiceAttribute,
    ServiceAttributeValue,
)


# =========================
# Service Category
# =========================
@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name_ar',
        'name_en',
        'slug',
        'is_featured',
        'sort_order',
        'is_active',
        'created_at',
    )
    list_filter = ('is_featured', 'is_active')
    search_fields = ('name_ar', 'name_en', 'slug')
    prepopulated_fields = {'slug': ('name_en',)}
    ordering = ('sort_order', 'name_ar')


# =========================
# Service Subcategory
# =========================
@admin.register(ServiceSubcategory)
class ServiceSubcategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name_ar',
        'name_en',
        'category',
        'slug',
        'sort_order',
        'is_active',
    )
    list_filter = ('category', 'is_active')
    search_fields = ('name_ar', 'name_en', 'slug')
    prepopulated_fields = {'slug': ('name_en',)}
    ordering = ('category', 'sort_order', 'name_ar')


# =========================
# Inline Images
# =========================
class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ('image', 'caption_ar', 'caption_en', 'sort_order', 'is_primary')
    ordering = ('sort_order',)


# =========================
# Inline Attributes
# =========================
class ServiceAttributeValueInline(admin.TabularInline):
    model = ServiceAttributeValue
    extra = 1
    autocomplete_fields = ('attribute',)


# =========================
# Service
# =========================
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        'title_ar',
        'owner',
        'category',
        'subcategory',
        'pricing_type',
        'price',
        'status',
        'views_count',
        'is_active',
        'created_at',
    )
    list_filter = (
        'status',
        'pricing_type',
        'category',
        'subcategory',
        'is_active',
    )
    search_fields = (
        'title_ar',
        'title_en',
        'description_ar',
        'description_en',
    )
    prepopulated_fields = {'slug': ('title_en',)}
    readonly_fields = ('views_count',)
    autocomplete_fields = ('owner', 'category', 'subcategory')
    inlines = [ServiceImageInline, ServiceAttributeValueInline]
    ordering = ('-created_at',)

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'owner',
                'title_ar',
                'title_en',
                'slug',
                'description_ar',
                'description_en',
            )
        }),
        (_('Categorization'), {
            'fields': ('category', 'subcategory')
        }),
        (_('Pricing'), {
            'fields': ('pricing_type', 'price', 'currency')
        }),
        (_('Service Details'), {
            'fields': ('duration_minutes', 'max_participants')
        }),
        (_('Status & Moderation'), {
            'fields': ('status', 'rejection_reason', 'is_active')
        }),
        (_('Metrics'), {
            'fields': ('views_count',)
        }),
    )


# =========================
# Service Attribute
# =========================
@admin.register(ServiceAttribute)
class ServiceAttributeAdmin(admin.ModelAdmin):
    list_display = (
        'name_ar',
        'name_en',
        'attribute_type',
        'is_required',
        'sort_order',
        'is_active',
    )
    list_filter = ('attribute_type', 'is_required', 'is_active')
    search_fields = ('name_ar', 'name_en')
    ordering = ('sort_order', 'name_ar')


# =========================
# Service Attribute Value
# =========================
@admin.register(ServiceAttributeValue)
class ServiceAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('service', 'attribute', 'value')
    search_fields = (
        'service__title_ar',
        'service__title_en',
        'attribute__name_ar',
        'attribute__name_en',
    )
    autocomplete_fields = ('service', 'attribute')
