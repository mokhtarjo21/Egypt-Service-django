"""
Views for the services app.
"""

from django.db.models import Q
from rest_framework import viewsets, generics, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.decorators import method_decorator
from django.contrib.contenttypes.models import ContentType



from .models import ServiceCategory, ServiceSubcategory, Service, ServiceImage
from .serializers import (
    ServiceCategorySerializer,
    ServiceCategoryCreateSerializer,
    ServiceSubcategorySerializer,
    ServiceSubcategoryCreateSerializer,
    ServiceSerializer,
    ServiceDetailSerializer,
    ServiceCreateUpdateSerializer,
    ServiceImageUploadSerializer,
    AdminServiceSerializer,
    ServiceImageSerializer
)
from .filters import ServiceFilter
from apps.accounts.models import AdminAction
from apps.notifications.utils import send_notification_if_enabled
from django_ratelimit.decorators import ratelimit


from apps.core.permissions import IsAdminRoleOrReadOnly

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service categories.
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAdminRoleOrReadOnly]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ServiceCategoryCreateSerializer
        return ServiceCategorySerializer

    @action(detail=True, methods=['get'])
    def subcategories(self, request, slug=None):
        """
        Get subcategories for a specific category.
        """
        category = self.get_object()
        subcategories = category.subcategories.filter(is_active=True)
        serializer = ServiceSubcategorySerializer(subcategories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured categories.
        """
        featured = self.queryset.filter(is_featured=True)
        serializer = self.get_serializer(featured, many=True)
        return Response(serializer.data)


class ServiceSubcategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service subcategories.
    """
    queryset = ServiceSubcategory.objects.filter(is_active=True)
    serializer_class = ServiceSubcategorySerializer
    permission_classes = [IsAdminRoleOrReadOnly]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ServiceSubcategoryCreateSerializer
        return ServiceSubcategorySerializer


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for services.
    """
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ServiceFilter
    search_fields = ['title_ar', 'title_en', 'description_ar', 'description_en']
    ordering_fields = ['created_at', 'price', 'views_count']
    ordering = ['-created_at']
    lookup_field = 'slug'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
        
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ServiceDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ServiceCreateUpdateSerializer
        return ServiceSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.action == 'list':
            # Always return only approved services for the main listing
            queryset = queryset.filter(status='approved')
        elif self.action == 'retrieve':
            if not self.request.user.is_authenticated:
                queryset = queryset.filter(status='approved')
            elif self.request.user.role != 'admin':
                # Show approved services + user's own services for direct retrieval
                queryset = queryset.filter(
                    Q(status='approved') | Q(owner=self.request.user)
                )
        
        return queryset

    def perform_create(self, serializer):
        # Check subscription limits
        from apps.subscriptions.models import Subscription, SubscriptionUsage
        
        subscription = Subscription.objects.filter(user=self.request.user, status='active').first()
        
        if not subscription:
            # Free tier - check service count
            active_services = Service.objects.filter(owner=self.request.user, status='approved', is_active=True).count()
            if active_services >= 3:
                raise serializers.ValidationError('تم الوصول للحد الأقصى من الخدمات في الخطة المجانية')
        else:
            if not subscription.can_create_service():
                raise serializers.ValidationError('تم الوصول للحد الأقصى من الخدمات في خطتك الحالية')
        
        service = serializer.save(owner=self.request.user)
        
        # Update usage tracking
        if subscription:
            usage, created = SubscriptionUsage.objects.get_or_create(subscription=subscription)
            usage.services_count = Service.objects.filter(owner=self.request.user, is_active=True).count()
            usage.save()

    @action(detail=True, methods=['post'])
    def increment_views(self, request, slug=None):
        """
        Increment view count for a service.
        """
        service = self.get_object()
        service.views_count += 1
        service.save(update_fields=['views_count'])
        return Response({'views_count': service.views_count})

    @action(detail=False, methods=['get'])
    def my_services(self, request):
        """
        Get current user's services.
        """
        services = Service.objects.filter(owner=request.user, is_active=True)
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_images(self, request, slug=None):
        """
        Upload images for a service.
        """
        service = self.get_object()
        
        # Check ownership
        if service.owner != request.user and request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        images_data = request.FILES.getlist('images')
        if not images_data:
            return Response({'error': 'No images provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_images = []
        for i, image_file in enumerate(images_data):
            serializer = ServiceImageUploadSerializer(data={
                'image': image_file,
                'is_primary': i == 0 and not service.images.filter(is_primary=True).exists()
            })
            
            if serializer.is_valid():
                image = serializer.save(service=service, sort_order=service.images.count())
                created_images.append(ServiceImageSerializer(image).data)
        
        return Response({
            'message': f'{len(created_images)} images uploaded successfully',
            'images': created_images
        })

    @action(detail=True, methods=['delete'])
    def delete_image(self, request, slug=None):
        """
        Delete a service image.
        """
        service = self.get_object()
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response({'error': 'Image ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            image = service.images.get(id=image_id)
            if service.owner != request.user and request.user.role != 'admin':
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            image.delete()
            return Response({'message': 'Image deleted successfully'})
        except ServiceImage.DoesNotExist:
            return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)


class FeaturedServicesView(generics.ListAPIView):
    """
    Get featured services.
    """
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Service.objects.filter(
            is_active=True,
            status='approved',
            category__is_featured=True
        )[:10]


class ServiceSearchView(generics.ListAPIView):
    """
    Advanced service search.
    """
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ServiceFilter
    search_fields = ['title_ar', 'title_en', 'description_ar', 'description_en']
    ordering_fields = ['price', 'views_count', 'created_at']

    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True, status='approved')
        
        # Additional search logic can be added here
        query = self.request.query_params.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(title_ar__icontains=query) |
                Q(title_en__icontains=query) |
                Q(description_ar__icontains=query) |
                Q(description_en__icontains=query) |
                Q(owner__full_name__icontains=query)
            )
        
        return queryset


# Admin Views
class AdminServiceListView(generics.ListAPIView):
    """
    Admin view to list services by status.
    """
    serializer_class = AdminServiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title_ar', 'title_en', 'owner__full_name']
    ordering_fields = ['created_at', 'price', 'views_count']
    ordering = ['-created_at']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        if not self.request.user.role == 'admin':
            return Service.objects.none()

        status_filter = self.request.query_params.get('status', 'all')
        queryset = Service.objects.filter(is_active=True)

        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)

        return queryset


class AdminServiceRetrieveView(generics.RetrieveAPIView):
    """
    Admin view to retrieve a single service with full images.
    """
    serializer_class = AdminServiceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        if not self.request.user.role == 'admin':
            return Service.objects.none()
        return Service.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        if not request.user.role == 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().retrieve(request, *args, **kwargs)


@method_decorator(ratelimit(key='user', rate='20/m', method='POST'), name='post')
class AdminServiceStatusUpdateView(generics.GenericAPIView):
    """
    Admin view to approve/reject services.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, service_id):
        if not request.user.role == 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            service = Service.objects.get(id=service_id)
            action = request.data.get('action')  # 'approve' or 'reject'
            reason = request.data.get('reason', '')
            
            if action not in ['approve', 'reject']:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
            
            old_status = service.status
            
            if action == 'approve':
                service.status = 'approved'
                action_type = 'service_approve'
            else:
                service.status = 'rejected'
                service.rejection_reason = reason
                action_type = 'service_reject'
            
            service.save()

            # Ping search engines when a service is approved (non-blocking)
            if action == 'approve':
                from .utils import notify_search_engines
                import threading
                threading.Thread(target=notify_search_engines, daemon=True).start()
            
            # Log admin action
            AdminAction.objects.create(
                admin=request.user,
                action_type=action_type,
                target_user=service.owner,
                content_type=ContentType.objects.get_for_model(Service),
                object_id=service.id,
                reason=reason,
                notes=f"Service {action}d: {service.title_ar}",
                ip_address=request.META.get('REMOTE_ADDR', ''),
            )
            
            # Send notification to service owner
            if action == 'approve':
                send_notification_if_enabled(
                    recipient=service.owner,
                    notification_type='service_approved',
                    title_ar='تمت الموافقة على خدمتك',
                    title_en='Your service has been approved',
                    message_ar=f'تمت الموافقة على خدمة "{service.title_ar}" وهي الآن متاحة للعملاء.',
                    message_en=f'Your service "{service.title_en}" has been approved and is now live.',
                    related_object=service
                )
            else:
                send_notification_if_enabled(
                    recipient=service.owner,
                    notification_type='service_rejected',
                    title_ar='تم رفض خدمتك',
                    title_en='Your service has been rejected',
                    message_ar=f'تم رفض خدمة "{service.title_ar}". السبب: {reason}',
                    message_en=f'Your service "{service.title_en}" has been rejected. Reason: {reason}',
                    related_object=service
                )
            
            return Response({
                'message': f'Service {action}d successfully',
                'service': AdminServiceSerializer(service).data
            })
            
        except Service.DoesNotExist:
            return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)

