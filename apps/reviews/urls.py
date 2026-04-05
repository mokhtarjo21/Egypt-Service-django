from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'reviews', views.ReviewViewSet, basename='review')

app_name = 'reviews'

urlpatterns = [
    path('', include(router.urls)),
]