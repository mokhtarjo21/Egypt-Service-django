from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'core'

router = DefaultRouter()
router.register(r'geo/governorates', views.ProvinceViewSet, basename='governorates')
router.register(r'geo/centers', views.CityViewSet, basename='centers')

urlpatterns = [
    path('', views.health_check, name='health-check'),
    path('', include(router.urls)),
]