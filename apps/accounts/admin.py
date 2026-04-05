from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    User,
    OTPCode,
    LoginAttempt,
    UserSession,
    UserProfile,
    UserDocument,
    AdminAction,
    TOTPSecret,
    UserDevice,
    SecurityAlert
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""

    list_display = (
        'full_name', 'phone_number', 'email', 'status', 'role', 
        'is_active', 'is_staff', 'is_phone_verified', 'email_verified', 'date_joined'
    )
    list_filter = ('status', 'role', 'is_active', 'is_staff', 'is_phone_verified', 'gender')
    search_fields = ('full_name', 'phone_number', 'email')
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')

    fieldsets = (
        (_('Basic Info'), {'fields': ('full_name', 'email', 'phone_number', 'password')}),
        (_('Personal Info'), {'fields': ('date_of_birth', 'gender', 'avatar', 'bio', 'governorate', 'center')}),
        (_('Permissions & Status'), {'fields': ('status', 'role', 'is_active', 'is_staff', 'is_superuser',
                                                'is_phone_verified', 'email_verified', 'groups', 'user_permissions')}),
        (_('Important Dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Documents'), {'fields': ('id_document', 'id_document_back')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('full_name', 'phone_number', 'email', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'years_experience', 'preferred_language', 'rating', 'total_reviews')
    search_fields = ('user__full_name', 'business_name')
    list_filter = ('preferred_language', 'notifications_enabled', 'marketing_emails')


@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'status', 'verified_at', 'verified_by')
    list_filter = ('document_type', 'status')
    search_fields = ('user__full_name',)
    readonly_fields = ('verified_at', 'verified_by')


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'purpose', 'expires_at', 'attempts', 'is_used')
    list_filter = ('purpose', 'is_used')
    search_fields = ('user__full_name', 'user__phone_number')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'ip_address', 'success', 'failure_reason', 'created_at')
    list_filter = ('success',)
    search_fields = ('phone_number', 'ip_address', 'user_agent')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'ip_address', 'is_active', 'last_activity')
    list_filter = ('is_active',)
    search_fields = ('user__full_name', 'session_key', 'ip_address')


@admin.register(AdminAction)
class AdminActionAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action_type', 'target_user', 'ip_address', 'created_at')
    list_filter = ('action_type',)
    search_fields = ('admin__full_name', 'target_user__full_name', 'reason')


@admin.register(TOTPSecret)
class TOTPSecretAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'last_used')
    search_fields = ('user__full_name',)


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'device_fingerprint', 'ip_address', 'is_trusted', 'last_seen')
    list_filter = ('is_trusted',)
    search_fields = ('user__full_name', 'device_name', 'device_fingerprint', 'ip_address')


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert_type', 'ip_address', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'is_resolved')
    search_fields = ('user__full_name', 'ip_address', 'user_agent', 'message')
