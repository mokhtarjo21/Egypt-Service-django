"""
Serializers for the teams app.
"""

from rest_framework import serializers
from .models import Organization, OrganizationMember, OrganizationRole
from apps.accounts.serializers import UserSerializer


class OrganizationRoleSerializer(serializers.ModelSerializer):
    """
    Serializer for OrganizationRole model.
    """
    class Meta:
        model = OrganizationRole
        fields = [
            'id', 'name', 'can_manage_services', 'can_manage_bookings',
            'can_manage_messaging', 'can_view_analytics', 'can_manage_members',
            'can_manage_finances'
        ]


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer for Organization model.
    """
    owner = UserSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name_ar', 'name_en', 'description_ar', 'description_en',
            'owner', 'logo', 'business_license', 'tax_number',
            'auto_approve_members', 'max_members', 'member_count', 'created_at'
        ]


class OrganizationMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for OrganizationMember model.
    """
    user = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    role = OrganizationRoleSerializer(read_only=True)
    
    class Meta:
        model = OrganizationMember
        fields = [
            'id', 'organization', 'user', 'role', 'status',
            'invited_at', 'joined_at'
        ]


class OrganizationInviteSerializer(serializers.Serializer):
    """
    Serializer for organization invites.
    """
    organization = serializers.UUIDField()
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    role = serializers.CharField()
    message = serializers.CharField(required=False)