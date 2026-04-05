"""
Sitemaps for the services app.
Generates dynamic sitemap entries for approved services and categories.
"""

from django.contrib.sitemaps import Sitemap
from django.conf import settings
from .models import Service, ServiceCategory, ServiceSubcategory


class ServiceSitemap(Sitemap):
    """
    Sitemap for individual approved services.
    Each entry points to the frontend service detail page.
    """
    changefreq = "weekly"
    priority = 0.9
    protocol = "https"

    def items(self):
        return Service.objects.filter(
            status='approved',
            is_active=True
        ).select_related('owner').order_by('-updated_at')

    def location(self, obj):
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        return f"{frontend_url}/services/{obj.slug}"

    def lastmod(self, obj):
        return obj.updated_at


class ServiceCategorySitemap(Sitemap):
    """
    Sitemap for service categories (browse pages).
    """
    changefreq = "monthly"
    priority = 0.7
    protocol = "https"

    def items(self):
        return ServiceCategory.objects.filter(is_active=True).order_by('sort_order')

    def location(self, obj):
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        return f"{frontend_url}/services?category={obj.slug}"

    def lastmod(self, obj):
        return obj.updated_at


class StaticPagesSitemap(Sitemap):
    """
    Sitemap for static pages (Home, About, Contact, etc.).
    """
    changefreq = "monthly"
    priority = 0.6
    protocol = "https"

    # List of static frontend routes
    static_pages = [
        ('/', 1.0),
        ('/services', 0.9),
        ('/about', 0.5),
        ('/contact', 0.5),
        ('/help', 0.4),
    ]

    def items(self):
        return self.static_pages

    def location(self, item):
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        return f"{frontend_url}{item[0]}"

    def priority(self, item):
        return item[1]
