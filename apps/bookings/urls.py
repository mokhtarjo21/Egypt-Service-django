"""
Booking URLs for Egyptian Service Marketplace.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BookingViewSet

app_name = 'bookings'

router = DefaultRouter()
router.register('', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]