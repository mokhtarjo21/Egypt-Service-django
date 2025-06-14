from .views import *
from django.urls import path, include


urlpatterns = [
    path('', services.as_view(),name='services'),  # هذا يضيف المسارات تلقائيًا
    path('<pk>', services.as_view(), name='get_all_services'),
]
