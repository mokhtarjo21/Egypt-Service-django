"""
Messaging models for Egyptian Service Marketplace.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.services.models import Service

User = get_user_model()


class Conversation(BaseModel):
    """
    Conversation between users about a service.
    """
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name=_('Service')
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='customer_conversations',
        verbose_name=_('Customer')
    )
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='provider_conversations',
        verbose_name=_('Provider')
    )
    subject = models.CharField(_('Subject'), max_length=200)
    is_archived = models.BooleanField(_('Archived'), default=False)
    last_message_at = models.DateTimeField(_('Last message at'), null=True, blank=True)

    class Meta:
        verbose_name = _('Conversation')
        verbose_name_plural = _('Conversations')
        ordering = ['-last_message_at']
        unique_together = ['service', 'customer', 'provider']

    def __str__(self):
        return f"{self.subject} - {self.customer.full_name} & {self.provider.full_name}"

    @property
    def unread_count_for_customer(self):
        return self.messages.filter(sender=self.provider, is_read=False).count()

    @property
    def unread_count_for_provider(self):
        return self.messages.filter(sender=self.customer, is_read=False).count()


class Message(BaseModel):
    """
    Individual messages within conversations.
    """
    MESSAGE_TYPE_CHOICES = [
        ('text', _('Text')),
        ('image', _('Image')),
        ('file', _('File')),
        ('system', _('System')),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Conversation')
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('Sender')
    )
    message_type = models.CharField(
        _('Message type'),
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    content = models.TextField(_('Content'))
    attachment = models.FileField(
        _('Attachment'),
        upload_to='message_attachments/',
        null=True,
        blank=True
    )
    is_read = models.BooleanField(_('Read'), default=False)
    read_at = models.DateTimeField(_('Read at'), null=True, blank=True)
    
    # Typing indicator support
    is_typing = models.BooleanField(_('Is typing'), default=False)
    typing_updated_at = models.DateTimeField(_('Typing updated at'), null=True, blank=True)

    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.full_name}: {self.content[:50]}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update conversation's last_message_at
        self.conversation.last_message_at = self.created_at
        self.conversation.save(update_fields=['last_message_at'])


class MessageReport(BaseModel):
    """
    Reports for inappropriate messages.
    """
    REASON_CHOICES = [
        ('spam', _('Spam')),
        ('harassment', _('Harassment')),
        ('inappropriate', _('Inappropriate Content')),
        ('fraud', _('Fraud/Scam')),
        ('other', _('Other')),
    ]
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_reports'
    )
    reason = models.CharField(
        _('Reason'),
        max_length=15,
        choices=REASON_CHOICES
    )
    description = models.TextField(_('Description'), blank=True)
    status = models.CharField(
        _('Status'),
        max_length=10,
        choices=[
            ('pending', _('Pending')),
            ('resolved', _('Resolved')),
            ('dismissed', _('Dismissed')),
        ],
        default='pending'
    )
    
    class Meta:
        verbose_name = _('Message Report')
        verbose_name_plural = _('Message Reports')
        unique_together = ['message', 'reporter']
        ordering = ['-created_at']

    def __str__(self):
        return f"Report by {self.reporter.full_name} - {self.get_reason_display()}"