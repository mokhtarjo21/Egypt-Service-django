from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Service

from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from .models import Service
from .serializers import *

class ApprovedServiceListView(generics.ListAPIView):
    serializer_class = getServiceSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'description']
    filterset_fields = ['governorate']

    def get_queryset(self):
        queryset = Service.objects.filter(status='Approved').select_related('user')

        # فلترة السعر من باراميترات الـ GET
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset
class PendingServiceViewSet(ReadOnlyModelViewSet):
    queryset = Service.objects.filter(status='pending')
    serializer_class = ServiceSerializer

class PendingServiceListView(generics.ListAPIView):
    queryset = Service.objects.filter(status='pending')
    serializer_class = ServiceSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']

    def get_queryset(self):
        return Service.objects.filter(status='pending').select_related('user')

class services(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]
    def get(self, request):
        services = Service.objects.all()
        serializer = getServiceSerializer(services, many=True)
        return Response(serializer.data)

    def post(self, request):
        print("User:", request.user)  # طباعة المستخدم الحالي
        print("Request Method:", request.method)
        print("Request Data:", request.data)  # طباعة البيانات الواردة
        serializer = ServiceSerializer(data=request.data, context={'request': request})  # أضف الـ context هنا
        if serializer.is_valid():
            serializer.save(user=request.user)
            services = Service.objects.all()
            serializer1 = getServiceSerializer(services, many=True)
            return Response(serializer1.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk):
        try:
            service = Service.objects.get(pk=pk)
            service.delete()
            return Response({'message': 'Service deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Service.DoesNotExist:
            return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)
    def patch(self, request, pk):
        try:
            print("Request Data:", request.data) 
            service = Service.objects.get(pk=pk)
            status1 = request.data.get('status')
            print("Status:", status1)
            if status1 not in ['Pending', 'Approved', 'Rejected']:
                return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
            service.status = status1
            service.save()
            services = Service.objects.all()
            serializer1 = getServiceSerializer(services, many=True)
            cache.delete('products_list')

            return Response(serializer1.data, status=status.HTTP_200_OK)
            
        except Service.DoesNotExist:
            return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)