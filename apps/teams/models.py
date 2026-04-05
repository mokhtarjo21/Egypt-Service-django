"""
Team and organization models for Egyptian Service Marketplace.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import BaseModel
from apps.services.models import Service

User = get_user_model()


class Organization(BaseModel):
    """
    Organizations for team-based service providers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name_ar = models.CharField(_('Arabic name'), max_length=200)
    name_en = models.CharField(_('English name'), max_length=200, blank=True)
    description_ar = models.TextField(_('Arabic description'), blank=True)
    description_en = models.TextField(_('English description'), blank=True)
    
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_organizations'
    )
    logo = models.ImageField(_('Logo'), upload_to='organizations/logos/', null=True, blank=True)
    
    # Business information
    business_license = models.CharField(_('Business license'), max_length=100, blank=True)
    tax_number = models.CharField(_('Tax number'), max_length=50, blank=True)
    
    # Settings
    auto_approve_members = models.BooleanField(_('Auto approve members'), default=False)
    max_members = models.PositiveIntegerField(_('Max members'), default=10)
    
    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        ordering = ['name_ar']

    def __str__(self):
        return self.name_ar

    @property
    def member_count(self):
        return self.members.filter(is_active=True).count()


class OrganizationRole(BaseModel):
    """
    Roles within organizations.
    """
    ROLE_CHOICES = [
        ('owner', _('Owner')),
        ('manager', _('Manager')),
        ('staff', _('Staff')),
    ]

    name = models.CharField(_('Role name'), max_length=20, choices=ROLE_CHOICES)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='roles'
    )
    
    # Permissions
    can_manage_services = models.BooleanField(_('Manage services'), default=False)
    can_manage_bookings = models.BooleanField(_('Manage bookings'), default=False)
    can_manage_messaging = models.BooleanField(_('Manage messaging'), default=False)
    can_view_analytics = models.BooleanField(_('View analytics'), default=False)
    can_manage_members = models.BooleanField(_('Manage members'), default=False)
    can_manage_finances = models.BooleanField(_('Manage finances'), default=False)
    
    class Meta:
        verbose_name = _('Organization Role')
        verbose_name_plural = _('Organization Roles')
        unique_together = ['organization', 'name']

    def __str__(self):
        return f"{self.organization.name_ar} - {self.get_name_display()}"


class OrganizationMember(BaseModel):
    """
    Organization membership.
    """
    STATUS_CHOICES = [
        ('invited', _('Invited')),
        ('active', _('Active')),
        ('suspended', _('Suspended')),
        ('left', _('Left')),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organization_memberships'
    )
    role = models.ForeignKey(
        OrganizationRole,
        on_delete=models.CASCADE
    )
    status = models.CharField(
        _('Status'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='invited'
    )
    
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organization_invites_sent'
    )
    invited_at = models.DateTimeField(_('Invited at'), default=timezone.now)
    joined_at = models.DateTimeField(_('Joined at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Organization Member')
        verbose_name_plural = _('Organization Members')
        unique_together = ['organization', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.full_name} @ {self.organization.name_ar}"


class ServiceAssignment(BaseModel):
    """
    Service assignments to organization members.
    """
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    member = models.ForeignKey(
        OrganizationMember,
        on_delete=models.CASCADE,
        related_name='service_assignments'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='service_assignments_made'
    )
    
    # Permissions for this specific service
    can_edit = models.BooleanField(_('Can edit'), default=True)
    can_message = models.BooleanField(_('Can message'), default=True)
    can_book = models.BooleanField(_('Can manage bookings'), default=True)
    
    class Meta:
        verbose_name = _('Service Assignment')
        verbose_name_plural = _('Service Assignments')
        unique_together = ['service', 'member']

    def __str__(self):
        return f"{self.service.title_ar} → {self.member.user.full_name}"