"""
Serializers for the accounts app.
"""

import hashlib
import secrets
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from django.core.exceptions import ValidationError

from .models import OTPCode, LoginAttempt
from apps.core.serializers import ProvinceSerializer, CitySerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    governorate = ProvinceSerializer(read_only=True)
    center = CitySerializer(read_only=True)
    active_subscription = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone_number', 'full_name', 'avatar', 'bio',
            'governorate', 'center', 'status', 'is_phone_verified', 'email_verified',
            'date_joined', 'gender', 'date_of_birth', 'role',
            'active_subscription', 'user_type',
        ]
        read_only_fields = ['id', 'status', 'is_phone_verified', 'email_verified', 'date_joined']

    def get_active_subscription(self, obj):
        """Return the user's current active subscription info, if any."""
        try:
            from apps.subscriptions.models import Subscription
            sub = Subscription.objects.filter(
                user=obj, status='active'
            ).select_related('plan').order_by('-created_at').first()
            if sub:
                return {
                    'id': str(sub.id),
                    'plan_type': sub.plan.plan_type,
                    'plan_name_ar': sub.plan.name_ar,
                    'plan_name_en': sub.plan.name_en,
                    'status': sub.status,
                    'current_period_end': sub.current_period_end,
                }
        except Exception:
            pass
        return None

    def get_user_type(self, obj):
        """
        Derive a user_type for the frontend:
        - 'admin' if they have admin role
        - 'provider' if they have an active paid subscription or have any services
        - 'user' otherwise
        """
        if obj.role == 'admin':
            return 'admin'
        try:
            from apps.subscriptions.models import Subscription
            has_sub = Subscription.objects.filter(
                user=obj, status='active'
            ).exclude(plan__plan_type='free').exists()
            if has_sub:
                return 'provider'
        except Exception:
            pass
        try:
            if obj.services_provided.filter(is_active=True).exists():
                return 'provider'
        except Exception:
            pass
        return 'user'


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Admin serializer for User model with additional fields.
    """
    governorate = ProvinceSerializer(read_only=True)
    center = CitySerializer(read_only=True)
    services_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone_number', 'full_name', 'avatar', 'bio',
            'governorate', 'center', 'status', 'role', 'is_phone_verified',
            'email_verified', 'date_joined', 'last_login', 'rejection_reason',
            'services_count', 'documents_count', 'documents',
            'id_document', 'id_document_back',
        ]

    def get_services_count(self, obj):
        return obj.services_provided.filter(is_active=True).count()

    def get_documents_count(self, obj):
        return obj.documents.filter(is_active=True).count()

    def get_documents(self, obj):
        request = self.context.get('request')
        result = []

        # -- Documents uploaded via IDDocumentUploadView (stored on User model directly) --
        def build_url(file_field):
            try:
                if file_field and file_field.name:
                    return request.build_absolute_uri(file_field.url) if request else file_field.url
            except Exception:
                pass
            return None

        if obj.id_document or obj.id_document_back:
            result.append({
                'id': str(obj.id) + '_id',
                'document_type': 'national_id',
                'document_type_display': 'بطاقة الهوية الوطنية',
                'status': obj.status if obj.status in ('pending', 'verified', 'rejected') else 'pending',
                'rejection_reason': obj.rejection_reason or '',
                'created_at': None,
                'document_front_url': build_url(obj.id_document),
                'document_back_url': build_url(obj.id_document_back),
            })

        # -- Documents from the UserDocument model (extra uploads) --
        try:
            for doc in obj.documents.all().order_by('-created_at'):
                result.append({
                    'id': str(doc.id),
                    'document_type': doc.document_type,
                    'document_type_display': doc.get_document_type_display(),
                    'status': doc.status,
                    'rejection_reason': doc.rejection_reason,
                    'created_at': doc.created_at,
                    'document_front_url': build_url(doc.document_front),
                    'document_back_url': build_url(doc.document_back) if doc.document_back else None,
                })
        except Exception:
            pass

        return result


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """
    Admin serializer for updating user status.
    """
    class Meta:
        model = User
        fields = ['status', 'role', 'rejection_reason']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    phone_number = PhoneNumberField()
    id_document = serializers.FileField(required=False)
    id_document_back = serializers.FileField(required=False)

    class Meta:
        model = User
        fields = [
            'phone_number', 'full_name', 'email', 'governorate', 'center',
            'password', 'password_confirm', 'id_document', 'id_document_back'
        ]

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate password strength
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})
            
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    phone_number = PhoneNumberField()
    password = serializers.CharField()


class GoogleLoginSerializer(serializers.Serializer):
    """
    Serializer for Google Login/Signup.
    """
    id_token = serializers.CharField(required=True)
    role = serializers.ChoiceField(
        choices=User.USER_ROLE_CHOICES, 
        required=False,
        default='user',
        help_text="Role if this is a new user registration"
    )


class OTPSendSerializer(serializers.Serializer):
    """
    Serializer for sending OTP.
    """
    phone_number = PhoneNumberField()
    purpose = serializers.ChoiceField(choices=OTPCode._meta.get_field('purpose').choices)


class OTPVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying OTP.
    """
    phone_number = PhoneNumberField()
    code = serializers.CharField(min_length=6, max_length=6)
    purpose = serializers.ChoiceField(choices=OTPCode._meta.get_field('purpose').choices)


class PhoneChangeRequestSerializer(serializers.Serializer):
    """
    Serializer to request a phone number change.
    """
    new_phone_number = PhoneNumberField()

    def validate_new_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value


class PhoneChangeVerifySerializer(serializers.Serializer):
    """
    Serializer to verify the phone number change using OTP.
    """
    new_phone_number = PhoneNumberField()
    code = serializers.CharField(min_length=6, max_length=6)


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    phone_number = PhoneNumberField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    phone_number = PhoneNumberField()
    code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField(min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
            
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = User
        fields = [
            'full_name', 'email', 'bio', 'avatar', 'date_of_birth', 
            'gender', 'governorate', 'center'
        ]


class IDDocumentUploadSerializer(serializers.Serializer):
    """
    Serializer for ID document upload.
    """
    id_document = serializers.FileField()
    id_document_back = serializers.FileField(required=False)


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField(min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
            
        return attrs

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value