"""
Serializers for the services app.
"""

from rest_framework import serializers
from .models import (
    ServiceCategory,
    ServiceSubcategory,
    Service,
    ServiceImage
)
from apps.accounts.serializers import UserSerializer
from apps.core.serializers import ProvinceSerializer, CitySerializer


class ServiceCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for ServiceCategory model.
    """
    services_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCategory
        fields = [
            'id', 'name_ar', 'name_en', 'slug', 'description_ar', 'description_en',
            'icon', 'color', 'is_featured', 'services_count'
        ]
        read_only_fields = ['slug', 'services_count']

    def get_services_count(self, obj):
        return obj.services.filter(is_active=True, status='approved').count()


class ServiceCategoryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating ServiceCategory.
    """
    class Meta:
        model = ServiceCategory
        fields = [
            'name_ar', 'name_en', 'description_ar', 'description_en',
            'icon', 'color', 'is_featured'
        ]


class ServiceSubcategorySerializer(serializers.ModelSerializer):
    """
    Serializer for ServiceSubcategory model.
    """
    category = ServiceCategorySerializer(read_only=True)
    services_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceSubcategory
        fields = [
            'id', 'name_ar', 'name_en', 'slug', 'description_ar', 'description_en',
            'category', 'services_count'
        ]
        read_only_fields = ['slug', 'services_count', 'category']

    def get_services_count(self, obj):
        return obj.services.filter(is_active=True, status='approved').count()


class ServiceSubcategoryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating ServiceSubcategory.
    """
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(), source='category', write_only=True
    )

    class Meta:
        model = ServiceSubcategory
        fields = [
            'name_ar', 'name_en', 'description_ar', 'description_en',
            'category_id'
        ]


class ServiceImageSerializer(serializers.ModelSerializer):
    """
    Serializer for ServiceImage model.
    """
    image = serializers.SerializerMethodField()

    class Meta:
        model = ServiceImage
        fields = [
            'id',
            'image',
            'caption_ar',
            'caption_en',
            'sort_order',
            'is_primary'
        ]

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for Service model (list view).
    """
    owner = UserSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    subcategory = ServiceSubcategorySerializer(read_only=True)
    governorate = ProvinceSerializer(read_only=True)
    center = CitySerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id', 'slug', 'title_ar', 'title_en', 'description_ar', 'description_en',
            'owner', 'category', 'subcategory', 'pricing_type', 'price', 'currency',
            'governorate', 'center', 'status', 'views_count', 'primary_image', 'created_at'
        ]

    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return ServiceImageSerializer(primary_image,context=self.context).data
        first_image = obj.images.first()
        if first_image:
            return ServiceImageSerializer(first_image,context=self.context).data
        return None


class ServiceDetailSerializer(ServiceSerializer):
    """
    Detailed serializer for Service model (retrieve view).
    """
    images = ServiceImageSerializer(many=True, read_only=True)
    
    class Meta(ServiceSerializer.Meta):
        fields = ServiceSerializer.Meta.fields + [
            'images', 'rejection_reason'
        ]


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating services.
    """
    images = ServiceImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'title_ar', 'slug','title_en', 'description_ar', 'description_en',
            'category', 'subcategory', 'pricing_type', 'price', 'currency',
            'governorate', 'center', 'images'
        ]

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class ServiceImageUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading service images.
    """
    class Meta:
        model = ServiceImage
        fields = ['image', 'caption_ar', 'caption_en', 'is_primary']


class AdminServiceSerializer(serializers.ModelSerializer):
    """
    Admin serializer for Service model with additional fields.
    """
    owner = UserSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    subcategory = ServiceSubcategorySerializer(read_only=True)
    images_count = serializers.SerializerMethodField()
    images = ServiceImageSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'slug', 'title_ar', 'title_en', 'description_ar', 'description_en',
            'owner', 'category', 'subcategory', 'pricing_type', 'price', 'currency',
            'status', 'rejection_reason', 'views_count', 'created_at', 'images_count', 'images'
        ]

    def get_images_count(self, obj):
        return obj.images.count()