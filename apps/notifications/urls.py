from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet, basename='notification')


app_name = 'notifications'

urlpatterns = [
    path('', include(router.urls)),
    path('preferences/', views.NotificationPreferenceView.as_view(), name='preferences'),
]