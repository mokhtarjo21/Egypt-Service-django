from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    path('track/', views.track_event, name='track-event'),
    path('provider/', views.ProviderAnalyticsView.as_view(), name='provider-analytics'),
    path('admin/', views.AdminAnalyticsView.as_view(), name='admin-analytics'),
    path('export/', views.export_analytics_csv, name='export-csv'),
]