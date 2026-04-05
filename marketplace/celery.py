"""
Celery configuration for Egyptian Service Marketplace.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings.dev')

app = Celery('marketplace')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'send-notification-digest': {
        'task': 'apps.notifications.tasks.send_notification_digest',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-expired-bookings': {
        'task': 'apps.bookings.tasks.cleanup_expired_bookings',
        'schedule': 86400.0,  # Daily
    },
    'generate-analytics-reports': {
        'task': 'apps.analytics.tasks.generate_daily_reports',
        'schedule': 86400.0,  # Daily
    },
}

app.conf.timezone = 'Africa/Cairo'