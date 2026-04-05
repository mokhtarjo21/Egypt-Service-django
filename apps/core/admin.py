from django.contrib import admin
from .models import (
    Province,
    City,
    SystemConfiguration,
)


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name_en', 'code')
    search_fields = ('name_ar', 'name_en', 'code')
    ordering = ('name_ar',)
    list_per_page = 25


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name_en', 'province')
    list_filter = ('province',)
    search_fields = ('name_ar', 'name_en', 'province__name_ar')
    ordering = ('province', 'name_ar')
    list_per_page = 25


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'key',
        'is_public',
        'is_active',
        'created_at',
        'updated_at',
    )
    list_filter = ('is_public', 'is_active')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('key',)
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'description')
        }),
        ('Visibility', {
            'fields': ('is_public', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
