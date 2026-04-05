from django.urls import path

from . import views

app_name = 'recommendations'

urlpatterns = [
    path('services/<uuid:service_id>/', views.ServiceRecommendationsView.as_view(), name='service-recommendations'),
    path('sentiment/<uuid:provider_id>/', views.ProviderSentimentView.as_view(), name='provider-sentiment'),
]