from rest_framework import serializers
from .models import Service, ServiceImage
from users.serializers import CurrentUserSerializer
class ServiceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceImage
        fields = ['id', 'image', 'createdAt']

class ServiceSerializer(serializers.ModelSerializer):
    images = ServiceImageSerializer(many=True, required=False)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'user', 'title', 'description', 'price',
            'is_active', 'governorate', 'center', 'status',
            'createdAt', 'updatedAt', 'images'
        ]
        read_only_fields = ['status', 'createdAt', 'updatedAt']

    def create(self, validated_data):
        request = self.context['request']
        images = request.FILES.getlist('images')  # <-- الصور هنا
        service = Service.objects.create(**validated_data)

        for image in images:
            ServiceImage.objects.create(service=service, image=image)

        return service
class getServiceSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    userId = serializers.PrimaryKeyRelatedField(source='user', read_only=True)
    user = CurrentUserSerializer(read_only=True)  # تأكد أن عندك UserSerializer

    class Meta:
        model = Service
        fields = [
            'id', 'userId', 'title', 'description', 'price',
            'governorate', 'center', 'images', 'status',
            'createdAt', 'user'
        ]

    def get_images(self, obj):
        return [img.image.url for img in obj.images.all()]
