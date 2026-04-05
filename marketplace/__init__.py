# Egyptian Service Marketplace Backend
# Bilingual (AR/EN) service marketplace for Egypt

__version__ = '1.0.0'
__author__ = 'Marketplace Team'

# Celery app import for Django
from .celery import app as celery_app

__all__ = ('celery_app',)