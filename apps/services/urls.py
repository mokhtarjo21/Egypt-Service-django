from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'categories', views.ServiceCategoryViewSet, basename='category')
router.register(r'subcategories', views.ServiceSubcategoryViewSet, basename='subcategory')
router.register(r'services', views.ServiceViewSet, basename='service')

app_name = 'services'

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Additional endpoints
    path('featured/', views.FeaturedServicesView.as_view(), name='featured-services'),
    path('search/', views.ServiceSearchView.as_view(), name='service-search'),
    
    # Admin endpoints
    path('admin/services/', views.AdminServiceListView.as_view(), name='admin-services-list'),
    path('admin/services/<uuid:pk>/', views.AdminServiceRetrieveView.as_view(), name='admin-service-detail'),
    path('admin/services/<uuid:service_id>/status/', views.AdminServiceStatusUpdateView.as_view(), name='admin-service-status'),
]