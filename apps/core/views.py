"""
Core views for Egyptian Service Marketplace.
"""

from django.http import JsonResponse
from django.utils.translation import gettext as _
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .models import Province, City
from .serializers import ProvinceSerializer, CitySerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint.
    """
    return JsonResponse({
        'status': 'healthy',
        'message': _('Egyptian Service Marketplace API is running'),
        'version': '1.0.0'
    })


from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsAdminRoleOrReadOnly

class ProvinceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Egyptian governorates.
    """
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer
    permission_classes = [IsAdminRoleOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name_ar', 'name_en']
    ordering_fields = ['name_ar', 'name_en']


class CityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for centers/cities.
    """
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAdminRoleOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['province']
    search_fields = ['name_ar', 'name_en']
    ordering_fields = ['name_ar', 'name_en']

    def get_queryset(self):
        queryset = City.objects.all()
        gov_id = self.request.query_params.get('gov_id')
        if gov_id:
            queryset = queryset.filter(province_id=gov_id)
        return queryset