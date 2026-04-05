from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'badges', views.BadgeViewSet, basename='badges')
router.register(r'user-badges', views.UserBadgeViewSet, basename='user-badges')

app_name = 'trust'

urlpatterns = [
    path('', include(router.urls)),
    path('metrics/<uuid:user_id>/', views.TrustMetricsView.as_view(), name='trust-metrics'),
]