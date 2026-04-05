"""
Development settings for Egyptian Service Marketplace.
"""

from .base import *

# Development-specific settings
DEBUG = True

# Database (local PostgreSQL for development)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': env('DB_NAME', default='marketplace_dev'),
#         'USER': env('DB_USER', default='marketplace_user'),
#         'PASSWORD': env('DB_PASSWORD', default='marketplace_pass'),
#         'HOST': env('DB_HOST', default='localhost'),
#         'PORT': env('DB_PORT', default='5432'),
#     }
# }

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Email Backend - Console for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Media files - Local storage for development
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files - Local storage for development
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Cache - Simple cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Debug Toolbar (optional)
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
        INTERNAL_IPS = ['127.0.0.1', '::1']
    except ImportError:
        pass

# Django Extensions
INSTALLED_APPS += ['django_extensions']

# Logging - More verbose for development
LOGGING['loggers']['marketplace']['level'] = 'DEBUG'
LOGGING['handlers']['console']['level'] = 'DEBUG'