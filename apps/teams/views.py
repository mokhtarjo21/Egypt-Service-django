"""
Views for the teams app.
"""

from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Organization, OrganizationMember, OrganizationRole
from .serializers import (
    OrganizationSerializer,
    OrganizationMemberSerializer,
    OrganizationInviteSerializer
)


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for organizations.
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(
            members__user=self.request.user,
            members__is_active=True,
            is_active=True
        )

    def perform_create(self, serializer):
        organization = serializer.save(owner=self.request.user)
        
        # Create default roles
        owner_role = OrganizationRole.objects.create(
            organization=organization,
            name='owner',
            can_manage_services=True,
            can_manage_bookings=True,
            can_manage_messaging=True,
            can_view_analytics=True,
            can_manage_members=True,
            can_manage_finances=True,
        )
        
        # Add owner as member
        OrganizationMember.objects.create(
            organization=organization,
            user=self.request.user,
            role=owner_role,
            status='active',
            joined_at=timezone.now()
        )


class OrganizationMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for organization members.
    """
    serializer_class = OrganizationMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only show members of organizations user belongs to
        user_orgs = Organization.objects.filter(
            members__user=self.request.user,
            members__is_active=True
        )
        return OrganizationMember.objects.filter(
            organization__in=user_orgs,
            is_active=True
        )


class OrganizationInviteView(generics.CreateAPIView):
    """
    Send organization invites.
    """
    serializer_class = OrganizationInviteSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # TODO: Implement invite logic
        return Response({'message': 'Invite sent successfully'})


class AcceptInviteView(generics.GenericAPIView):
    """
    Accept organization invite.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, invite_id):
        # TODO: Implement invite acceptance
        return Response({'message': 'Invite accepted successfully'})