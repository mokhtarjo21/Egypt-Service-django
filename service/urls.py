from .views import *
from django.urls import path, include


urlpatterns = [
    path('', services.as_view(),name='services'),  # هذا يضيف المسارات تلقائيًا
    path('<pk>', services.as_view(), name='get_all_services'),
    # path('pending/', PendingServiceViewSet.as_view({'get': 'list'}), name='pending_services'),
    path('pending/<pk>', PendingServiceViewSet.as_view({'get': 'retrieve'}), name='pending_service_detail'),
    path('pending/', PendingServiceListView.as_view(), name='pending-services'),    
    path('approved/', ApprovedServiceListView.as_view(), name='approved-services'),
]
