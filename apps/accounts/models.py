"""
Enhanced User accounts models for Egyptian Service Marketplace.
"""

import uuid
import hashlib
import secrets
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import FileExtensionValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import secrets
import base64
from cryptography.fernet import Fernet
from django.conf import settings

from apps.core.models import BaseModel, Province, City
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Enhanced custom user model for the marketplace.
    """
    USER_STATUS_CHOICES = [
        ('pending', _('Pending Verification')),
        ('verified', _('Verified')),
        ('rejected', _('Rejected')),
        ('suspended', _('Suspended')),
        ('blocked', _('Blocked')),
    ]
    
    USER_ROLE_CHOICES = [
        ('user', _('User')),
        ('admin', _('Administrator')),
    ]
    
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
    ]

    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('Email address'), unique=True, null=True, blank=True)
    phone_number = PhoneNumberField(_('Phone number'), unique=True)
    full_name = models.CharField(_('Full name'), max_length=100)
    
    # Location
    governorate = models.ForeignKey(
        Province, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_('Governorate')
    )
    center = models.ForeignKey(
        City, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_('Center')
    )
    
    # Profile Information
    date_of_birth = models.DateField(_('Date of birth'), null=True, blank=True)
    gender = models.CharField(
        _('Gender'), 
        max_length=1, 
        choices=GENDER_CHOICES, 
        blank=True
    )
    avatar = models.ImageField(_('Avatar'), upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(_('Bio'), max_length=500, blank=True)
    
    # Verification Documents
    id_document = models.FileField(
        _('ID Document'),
        upload_to='id_documents/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    id_document_back = models.FileField(
        _('ID Document Back'),
        upload_to='id_documents/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    
    # Account Status
    status = models.CharField(
        _('Status'),
        max_length=10,
        choices=USER_STATUS_CHOICES,
        default='pending'
    )
    role = models.CharField(
        _('Role'),
        max_length=10,
        choices=USER_ROLE_CHOICES,
        default='user'
    )
    rejection_reason = models.TextField(_('Rejection reason'), blank=True)
    
    # Verification Status
    is_active = models.BooleanField(_('Active'), default=True)
    is_staff = models.BooleanField(_('Staff status'), default=False)
    is_phone_verified = models.BooleanField(_('Phone verified'), default=False)
    email_verified = models.BooleanField(_('Email verified'), default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(_('Date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('Last login'), null=True, blank=True)
    
    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"

    @property
    def is_verified(self):
        return self.status == 'verified' and self.is_phone_verified

    @property
    def can_publish_services(self):
        """Check if user can publish new services."""
        return self.is_verified and self.status == 'verified'


class OTPCode(BaseModel):
    """
    OTP codes for phone verification.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    code_hash = models.CharField(_('Code hash'), max_length=128)
    purpose = models.CharField(
        _('Purpose'),
        max_length=20,
        choices=[
            ('registration', _('Registration')),
            ('login', _('Login')),
            ('password_reset', _('Password Reset')),
            ('phone_change', _('Phone Change')),
        ]
    )
    expires_at = models.DateTimeField(_('Expires at'))
    attempts = models.PositiveIntegerField(_('Attempts'), default=0)
    is_used = models.BooleanField(_('Used'), default=False)
    
    class Meta:
        verbose_name = _('OTP Code')
        verbose_name_plural = _('OTP Codes')
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired() and self.attempts < 5


class LoginAttempt(BaseModel):
    """
    Track login attempts for security.
    """
    phone_number = PhoneNumberField(_('Phone number'))
    ip_address = models.GenericIPAddressField(_('IP Address'))
    user_agent = models.TextField(_('User Agent'), blank=True)
    success = models.BooleanField(_('Success'), default=False)
    failure_reason = models.CharField(_('Failure reason'), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('Login Attempt')
        verbose_name_plural = _('Login Attempts')
        ordering = ['-created_at']


class UserSession(BaseModel):
    """
    Track user sessions.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(_('Session key'), max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(_('IP Address'))
    user_agent = models.TextField(_('User Agent'), blank=True)
    last_activity = models.DateTimeField(_('Last activity'), auto_now=True)
    is_active = models.BooleanField(_('Active'), default=True)
    
    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        ordering = ['-last_activity']


class UserProfile(BaseModel):
    """
    Extended user profile information.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    business_name = models.CharField(_('Business name'), max_length=200, blank=True)
    years_experience = models.PositiveIntegerField(_('Years of experience'), default=0)
    preferred_language = models.CharField(
        _('Preferred language'),
        max_length=2,
        choices=[('ar', 'Arabic'), ('en', 'English')],
        default='ar'
    )
    notifications_enabled = models.BooleanField(_('Notifications enabled'), default=True)
    marketing_emails = models.BooleanField(_('Marketing emails'), default=False)
    
    # Calculated fields
    rating = models.DecimalField(
        _('Average rating'),
        max_digits=3,
        decimal_places=2,
        default=0.00
    )
    total_reviews = models.PositiveIntegerField(_('Total reviews'), default=0)
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return f"Profile of {self.user.full_name}"


class UserDocument(BaseModel):
    """
    User verification documents.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('national_id', _('National ID')),
        ('passport', _('Passport')),
        ('business_license', _('Business License')),
        ('tax_certificate', _('Tax Certificate')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        _('Document type'),
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES
    )
    document_front = models.FileField(
        _('Document front'),
        upload_to='documents/private/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    document_back = models.FileField(
        _('Document back'),
        upload_to='documents/private/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    status = models.CharField(
        _('Status'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    rejection_reason = models.TextField(_('Rejection reason'), blank=True)
    verified_at = models.DateTimeField(_('Verified at'), null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_verified'
    )
    
    class Meta:
        verbose_name = _('User Document')
        verbose_name_plural = _('User Documents')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.get_document_type_display()}"


class AdminAction(BaseModel):
    """
    Track admin actions for audit purposes.
    """
    ACTION_TYPE_CHOICES = [
        ('user_verify', _('User Verified')),
        ('user_reject', _('User Rejected')),
        ('user_suspend', _('User Suspended')),
        ('user_block', _('User Blocked')),
        ('user_unblock', _('User Unblocked')),
        ('service_approve', _('Service Approved')),
        ('service_reject', _('Service Rejected')),
        ('service_suspend', _('Service Suspended')),
        ('document_approve', _('Document Approved')),
        ('document_reject', _('Document Rejected')),
        ('report_resolve', _('Report Resolved')),
        ('report_dismiss', _('Report Dismissed')),
    ]

    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='admin_actions'
    )
    action_type = models.CharField(
        _('Action type'),
        max_length=20,
        choices=ACTION_TYPE_CHOICES
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='admin_actions_received',
        null=True,
        blank=True
    )
    
    # Generic foreign key for any target object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id =  models.UUIDField()
    target_object = GenericForeignKey('content_type', 'object_id')
    
    reason = models.TextField(_('Reason'), blank=True)
    notes = models.TextField(_('Admin notes'), blank=True)
    ip_address = models.GenericIPAddressField(_('IP address'))
    
    class Meta:
        verbose_name = _('Admin Action')
        verbose_name_plural = _('Admin Actions')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admin.full_name} - {self.get_action_type_display()}"


class TOTPSecret(BaseModel):
    """
    TOTP secrets for 2FA.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='totp_secret'
    )
    encrypted_secret = models.TextField(_('Encrypted secret'))
    is_verified = models.BooleanField(_('Verified'), default=False)
    backup_codes = models.JSONField(_('Backup codes'), default=list)
    last_used = models.DateTimeField(_('Last used'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('TOTP Secret')
        verbose_name_plural = _('TOTP Secrets')

    def __str__(self):
        return f"TOTP for {self.user.full_name}"
    
    def encrypt_secret(self, secret):
        """Encrypt TOTP secret."""
        key = settings.SECRET_KEY[:32].encode()
        f = Fernet(base64.urlsafe_b64encode(key))
        self.encrypted_secret = f.encrypt(secret.encode()).decode()
    
    def decrypt_secret(self):
        """Decrypt TOTP secret."""
        key = settings.SECRET_KEY[:32].encode()
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.decrypt(self.encrypted_secret.encode()).decode()
    
    def generate_backup_codes(self):
        """Generate new backup codes."""
        codes = [secrets.token_hex(4).upper() for _ in range(10)]
        # Hash the codes before storing
        import hashlib
        hashed_codes = [hashlib.sha256(code.encode()).hexdigest() for code in codes]
        self.backup_codes = hashed_codes
        return codes  # Return unhashed codes for display


class UserDevice(BaseModel):
    """
    Track user devices and sessions.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='devices'
    )
    device_fingerprint = models.CharField(_('Device fingerprint'), max_length=64)
    device_name = models.CharField(_('Device name'), max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(_('IP Address'))
    user_agent = models.TextField(_('User Agent'))
    location = models.CharField(_('Location'), max_length=100, blank=True)
    is_trusted = models.BooleanField(_('Trusted device'), default=False)
    last_seen = models.DateTimeField(_('Last seen'), auto_now=True)
    
    class Meta:
        verbose_name = _('User Device')
        verbose_name_plural = _('User Devices')
        unique_together = ['user', 'device_fingerprint']
        ordering = ['-last_seen']

    def __str__(self):
        return f"{self.user.full_name} - {self.device_name or 'Unknown Device'}"


class SecurityAlert(BaseModel):
    """
    Security alerts for users.
    """
    ALERT_TYPE_CHOICES = [
        ('new_device', _('New Device Login')),
        ('new_location', _('New Location Login')),
        ('failed_login', _('Failed Login Attempt')),
        ('password_change', _('Password Changed')),
        ('2fa_disabled', _('2FA Disabled')),
        ('suspicious_activity', _('Suspicious Activity')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='security_alerts'
    )
    alert_type = models.CharField(
        _('Alert type'),
        max_length=20,
        choices=ALERT_TYPE_CHOICES
    )
    message = models.TextField(_('Alert message'))
    ip_address = models.GenericIPAddressField(_('IP Address'))
    user_agent = models.TextField(_('User Agent'), blank=True)
    is_resolved = models.BooleanField(_('Resolved'), default=False)
    resolved_at = models.DateTimeField(_('Resolved at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Security Alert')
        verbose_name_plural = _('Security Alerts')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.get_alert_type_display()}"