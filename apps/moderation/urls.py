from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'reports', views.ReportViewSet, basename='reports')
router.register(r'appeals', views.AppealViewSet, basename='appeals')
router.register(r'policies', views.PolicyVersionViewSet, basename='policies')
router.register(r'templates', views.ModerationTemplateViewSet, basename='templates')

app_name = 'moderation'

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.ModerationDashboardView.as_view(), name='moderation-dashboard'),
]