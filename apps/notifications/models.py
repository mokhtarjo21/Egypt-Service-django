"""
Notification models for Egyptian Service Marketplace.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from apps.core.models import BaseModel

User = get_user_model()


class Notification(BaseModel):
    """
    Notifications for users.
    """
    TYPE_CHOICES = [
        ('message', _('New Message')),
        ('booking', _('Booking Update')),
        ('review', _('New Review')),
        ('payment', _('Payment Update')),
        ('service_approved', _('Service Approved')),
        ('service_rejected', _('Service Rejected')),
        ('account_verified', _('Account Verified')),
        ('system', _('System Notification')),
        ('badge_earned', _('Badge Earned')),
        ('trust_update', _('Trust Update')),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Recipient')
    )
    notification_type = models.CharField(
        _('Type'),
        max_length=20,
        choices=TYPE_CHOICES
    )
    title_ar = models.CharField(_('Arabic title'), max_length=200)
    title_en = models.CharField(_('English title'), max_length=200, blank=True)
    message_ar = models.TextField(_('Arabic message'))
    message_en = models.TextField(_('English message'), blank=True)
    
    # Related object (optional)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=50, null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Status
    is_read = models.BooleanField(_('Read'), default=False)
    read_at = models.DateTimeField(_('Read at'), null=True, blank=True)
    
    # Delivery
    email_sent = models.BooleanField(_('Email sent'), default=False)
    sms_sent = models.BooleanField(_('SMS sent'), default=False)
    push_sent = models.BooleanField(_('Push notification sent'), default=False)

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.full_name} - {self.title_ar}"

    def mark_as_read(self):
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationTemplate(BaseModel):
    """
    Localized notification templates.
    """
    CHANNEL_CHOICES = [
        ('in_app', _('In-App')),
        ('email', _('Email')),
        ('sms', _('SMS')),
        ('push', _('Push')),
    ]

    event_type = models.CharField(_('Event type'), max_length=30)
    channel = models.CharField(_('Channel'), max_length=10, choices=CHANNEL_CHOICES)
    language = models.CharField(_('Language'), max_length=2, choices=[('ar', 'Arabic'), ('en', 'English')])
    
    subject_template = models.CharField(_('Subject template'), max_length=200, blank=True)
    body_template = models.TextField(_('Body template'))
    variables = models.JSONField(_('Template variables'), default=list)
    
    version = models.PositiveIntegerField(_('Version'), default=1)
    is_active = models.BooleanField(_('Active'), default=True)
    
    class Meta:
        verbose_name = _('Notification Template')
        verbose_name_plural = _('Notification Templates')
        unique_together = ['event_type', 'channel', 'language', 'version']
        ordering = ['event_type', 'channel', '-version']

    def __str__(self):
        return f"{self.event_type} - {self.channel} ({self.language})"


class NotificationPreference(BaseModel):
    """
    User notification preferences.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email preferences
    email_messages = models.BooleanField(_('Email for messages'), default=True)
    email_bookings = models.BooleanField(_('Email for bookings'), default=True)
    email_reviews = models.BooleanField(_('Email for reviews'), default=True)
    email_payments = models.BooleanField(_('Email for payments'), default=True)
    email_marketing = models.BooleanField(_('Marketing emails'), default=False)
    
    # SMS preferences
    sms_bookings = models.BooleanField(_('SMS for bookings'), default=True)
    sms_payments = models.BooleanField(_('SMS for payments'), default=True)
    sms_urgent = models.BooleanField(_('SMS for urgent notifications'), default=True)
    
    # Push notification preferences
    push_messages = models.BooleanField(_('Push for messages'), default=True)
    push_bookings = models.BooleanField(_('Push for bookings'), default=True)
    push_reviews = models.BooleanField(_('Push for reviews'), default=True)
    
    # Digest and timing preferences
    digest_frequency = models.CharField(
        _('Digest frequency'),
        max_length=10,
        choices=[
            ('none', _('None')),
            ('daily', _('Daily')),
            ('weekly', _('Weekly')),
        ],
        default='none'
    )
    quiet_hours_start = models.TimeField(_('Quiet hours start'), null=True, blank=True)
    quiet_hours_end = models.TimeField(_('Quiet hours end'), null=True, blank=True)
    timezone = models.CharField(_('Timezone'), max_length=50, default='Africa/Cairo')

    class Meta:
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')

    def __str__(self):
        return f"Preferences for {self.user.full_name}"