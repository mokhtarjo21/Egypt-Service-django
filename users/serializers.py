
   
from rest_framework import serializers
from .models import User, governorates, cities

class UserSerializer(serializers.ModelSerializer):
    governorates = serializers.SerializerMethodField()
    centers = serializers.SerializerMethodField()
    isAdmin = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='date_joined')
    class Meta:
        model = User
        fields = [
            'id',
            'fullName',
            'phoneNumber',
            'serviceType',
            'governorates',
            'centers',
            'bio',
            'idPhotoUrl',
            'idfPhotoUrl',
            'iduserPhotoUrl',
            'isVerified',
            'isPhoneVerified',
            'verificationStatus',
            'isAdmin',
            'isActive',
            'createdAt',
            'last_login',
            
        ]
    def get_governorates(self, obj):
        return [gov.governorate for gov in governorates.objects.filter(user=obj)]

    def get_centers(self, obj):
        return [city.city for city in cities.objects.filter(user=obj)]

    def get_isAdmin(self, obj):
        return obj.is_superuser

class GovernorateSerializer(serializers.ModelSerializer):
    class Meta:
        model = governorates
        fields = ['governorate']

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = cities
        fields = ['city']

class CurrentUserSerializer(serializers.ModelSerializer):
    governorates = serializers.SerializerMethodField()
    centers = serializers.SerializerMethodField()
    isAdmin = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='date_joined')
    
    class Meta:
        model = User
        fields = [
            'id',
            'fullName',
            'phoneNumber',
            'serviceType',
            'governorates',
            'centers',
            'bio',
            'idPhotoUrl',
            'idfPhotoUrl',
            'iduserPhotoUrl',
            'isVerified',
            'isPhoneVerified',
            'verificationStatus',
            'isAdmin',
            'isActive',
            'createdAt',
            'last_login',
        ]

    def get_governorates(self, obj):
        return [gov.governorate for gov in governorates.objects.filter(user=obj)]

    def get_centers(self, obj):
        return [city.city for city in cities.objects.filter(user=obj)]

    def get_isAdmin(self, obj):
        return obj.is_superuser



class UserRegisterSerializer(serializers.ModelSerializer):
    governorates = serializers.ListField(child=serializers.CharField(), write_only=True)
    centers = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = User
        fields = [
            'fullName', 'phoneNumber', 'password', 'serviceType',
            'idPhotoUrl', 'idfPhotoUrl', 'iduserPhotoUrl', 'bio',
            'governorates', 'centers'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        governorates_data = validated_data.pop('governorates', [])
        centers_data = validated_data.pop('centers', [])
        
        # إنشاء المستخدم وتشفير كلمة المرور
        user = User(
            fullName=validated_data['fullName'],
            phoneNumber=validated_data['phoneNumber'],
            serviceType=validated_data['serviceType'],
            idPhotoUrl=validated_data['idPhotoUrl'],
            idfPhotoUrl=validated_data['idfPhotoUrl'],
            iduserPhotoUrl=validated_data['iduserPhotoUrl'],
            bio=validated_data['bio'],
        )
        user.set_password(validated_data['password'])
        user.save()

        # ربط المحافظات بالمستخدم
        for gov in governorates_data:
            governorates.objects.create(user=user, governorate=gov)

        # ربط المدن بالمستخدم
        for city in centers_data:
            cities.objects.create(user=user, city=city)

        return user
    def to_internal_value(self, data):
            data = data.copy()

             # معالجة governorates و centers القادمين من FormData
            data.setlist('governorates', data.getlist('governorates[]'))
            data.setlist('centers', data.getlist('centers[]'))

            return super().to_internal_value(data)


class UserRegisterSerializer1(serializers.ModelSerializer):
    governorates = serializers.ListField(child=serializers.CharField(), write_only=True)
    centers = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = User
        fields = [
            'fullName', 'phoneNumber', 'password', 'serviceType',
            'idPhotoUrl', 'idfPhotoUrl', 'iduserPhotoUrl', 'bio',
            'governorates', 'centers'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        governorates_data = validated_data.pop('governorates', [])
        centers_data = validated_data.pop('centers', [])
        
        # إنشاء المستخدم وتشفير كلمة المرور
        user = User(
            fullName=validated_data['fullName'],
            phoneNumber=validated_data['phoneNumber'],
            serviceType=validated_data['serviceType'],
            idPhotoUrl=validated_data['idPhotoUrl'],
            idfPhotoUrl=validated_data['idfPhotoUrl'],
            iduserPhotoUrl=validated_data['iduserPhotoUrl'],
            bio=validated_data['bio'],
        )
        user.set_password(validated_data['password'])
        user.save()

        # ربط المحافظات بالمستخدم
        for gov in governorates_data:
            governorates.objects.create(user=user, governorate=gov)

        # ربط المدن بالمستخدم
        for city in centers_data:
            cities.objects.create(user=user, city=city)

        return user