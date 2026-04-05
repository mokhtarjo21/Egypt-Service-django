"""
Egyptian Service Marketplace URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.services.sitemaps import ServiceSitemap, ServiceCategorySitemap, StaticPagesSitemap

# =====================
# Sitemap Registry
# =====================
sitemaps = {
    'services': ServiceSitemap,
    'categories': ServiceCategorySitemap,
    'static': StaticPagesSitemap,
}


def robots_txt(request):
    """Serve robots.txt dynamically to allow full crawling and point to sitemap."""
    site_url = getattr(settings, 'SITE_URL', request.build_absolute_uri('/').rstrip('/'))
    content = f"""User-agent: *
Allow: /

# Sitemap
Sitemap: {site_url}/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')

# API URL patterns (no i18n prefix for API)
api_urlpatterns = [
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/services/', include('apps.services.urls')),
    path('api/v1/reviews/', include('apps.reviews.urls')),
    path('api/v1/messages/', include('apps.messages.urls')),
    path('api/v1/bookings/', include('apps.bookings.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/trust/', include('apps.trust.urls')),
    path('api/v1/recommendations/', include('apps.recommendations.urls')),
    path('api/v1/teams/', include('apps.teams.urls')),
    path('api/v1/subscriptions/', include('apps.subscriptions.urls')),
    path('api/v1/moderation/', include('apps.moderation.urls')),
    path('api/v1/health/', include('apps.core.urls')),
    
    # Monitoring endpoints
    path('metrics/', include('django_prometheus.urls')),
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Main URL patterns
urlpatterns = [
    # API routes (no i18n)
    *api_urlpatterns,

    # SEO — Sitemap & Robots.txt
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots-txt'),

    # Admin (with i18n)
    *i18n_patterns(
        path('admin/', admin.site.urls),
        path('rosetta/', include('rosetta.urls')),  # Translation interface
        prefix_default_language=False
    ),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]

# Admin site customization
admin.site.site_header = 'منصة الخدمات المصرية'
admin.site.site_title = 'Egyptian Marketplace Admin'
admin.site.index_title = 'إدارة المنصة'