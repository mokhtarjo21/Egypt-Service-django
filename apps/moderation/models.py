"""
Trust & Safety moderation models for Egyptian Service Marketplace.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from datetime import timedelta

from apps.core.models import BaseModel

User = get_user_model()


class PolicyVersion(BaseModel):
    """
    Versioned policy documents (Terms, Privacy, Community Guidelines).
    """
    POLICY_TYPE_CHOICES = [
        ('terms', _('Terms of Service')),
        ('privacy', _('Privacy Policy')),
        ('community', _('Community Guidelines')),
        ('safety', _('Safety Guidelines')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy_type = models.CharField(_('Policy type'), max_length=20, choices=POLICY_TYPE_CHOICES)
    version = models.CharField(_('Version'), max_length=20)
    title_ar = models.CharField(_('Arabic title'), max_length=200)
    title_en = models.CharField(_('English title'), max_length=200)
    content_ar = models.TextField(_('Arabic content'))
    content_en = models.TextField(_('English content'))
    
    # Versioning
    is_active = models.BooleanField(_('Active'), default=False)
    effective_date = models.DateTimeField(_('Effective date'))
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='policies_created'
    )
    
    # Change tracking
    change_summary = models.TextField(_('Change summary'), blank=True)
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions'
    )

    class Meta:
        verbose_name = _('Policy Version')
        verbose_name_plural = _('Policy Versions')
        unique_together = ['policy_type', 'version']
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.get_policy_type_display()} v{self.version}"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate other versions of the same policy type
            PolicyVersion.objects.filter(
                policy_type=self.policy_type,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)


class Report(BaseModel):
    """
    Enhanced reports with severity and SLA tracking.
    """
    REASON_CHOICES = [
        ('spam', _('Spam')),
        ('inappropriate', _('Inappropriate Content')),
        ('fake', _('Fake Service/Profile')),
        ('fraud', _('Fraud/Scam')),
        ('harassment', _('Harassment')),
        ('copyright', _('Copyright Violation')),
        ('pricing', _('Misleading Pricing')),
        ('location', _('Wrong Location')),
        ('quality', _('Poor Service Quality')),
        ('violence', _('Violence/Threats')),
        ('hate_speech', _('Hate Speech')),
        ('minor_safety', _('Minor Safety')),
        ('other', _('Other')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending Triage')),
        ('triaging', _('Under Triage')),
        ('assigned', _('Assigned to Moderator')),
        ('investigating', _('Under Investigation')),
        ('resolved', _('Resolved')),
        ('dismissed', _('Dismissed')),
        ('escalated', _('Escalated')),
    ]
    
    SEVERITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_made',
        verbose_name=_('Reporter')
    )
    reason = models.CharField(_('Reason'), max_length=15, choices=REASON_CHOICES)
    description = models.TextField(_('Description'))
    evidence = models.FileField(
        _('Evidence'),
        upload_to='reports/evidence/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'mp4', 'mov'])]
    )
    
    # Target object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    reported_object = GenericForeignKey('content_type', 'object_id')
    
    # Triage and assignment
    severity = models.CharField(_('Severity'), max_length=10, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_assigned',
        verbose_name=_('Assigned moderator')
    )
    
    # SLA tracking
    sla_due_at = models.DateTimeField(_('SLA due at'), null=True, blank=True)
    first_response_at = models.DateTimeField(_('First response at'), null=True, blank=True)
    resolved_at = models.DateTimeField(_('Resolved at'), null=True, blank=True)
    
    # Resolution
    resolution_notes = models.TextField(_('Resolution notes'), blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_resolved',
        verbose_name=_('Resolved by')
    )
    
    # Internal tracking
    internal_notes = models.TextField(_('Internal notes'), blank=True)
    escalation_reason = models.TextField(_('Escalation reason'), blank=True)

    class Meta:
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        ordering = ['sla_due_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'severity', 'sla_due_at']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"Report #{self.id.hex[:8]} - {self.get_reason_display()}"

    def save(self, *args, **kwargs):
        if not self.sla_due_at:
            # Set SLA based on severity
            sla_hours = {
                'critical': 2,
                'high': 24,
                'medium': 72,
                'low': 168,  # 1 week
            }
            self.sla_due_at = self.created_at + timedelta(hours=sla_hours[self.severity])
        
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return self.sla_due_at and timezone.now() > self.sla_due_at

    @property
    def time_to_sla(self):
        if self.sla_due_at:
            delta = self.sla_due_at - timezone.now()
            return delta if delta.total_seconds() > 0 else timedelta(0)
        return None


class ModerationAction(BaseModel):
    """
    Enhanced moderation actions with reason codes and appeals.
    """
    ACTION_TYPE_CHOICES = [
        ('warn', _('Warning Issued')),
        ('hide_content', _('Content Hidden')),
        ('reject_content', _('Content Rejected')),
        ('suspend_user', _('User Suspended')),
        ('block_user', _('User Blocked')),
        ('remove_content', _('Content Removed')),
        ('approve_content', _('Content Approved')),
        ('restore_content', _('Content Restored')),
        ('unblock_user', _('User Unblocked')),
        ('escalate', _('Escalated to Senior')),
    ]
    
    REASON_CODE_CHOICES = [
        ('SPAM_001', _('Commercial Spam')),
        ('SPAM_002', _('Repetitive Content')),
        ('INAP_001', _('Adult Content')),
        ('INAP_002', _('Violent Content')),
        ('INAP_003', _('Hate Speech')),
        ('FAKE_001', _('Fake Profile')),
        ('FAKE_002', _('Fake Service')),
        ('FRAU_001', _('Financial Fraud')),
        ('FRAU_002', _('Identity Theft')),
        ('HARA_001', _('Harassment')),
        ('HARA_002', _('Stalking')),
        ('COPY_001', _('Copyright Violation')),
        ('PRIC_001', _('Misleading Pricing')),
        ('QUAL_001', _('Poor Service Quality')),
        ('LOCA_001', _('Wrong Location')),
        ('SAFE_001', _('Safety Concern')),
        ('MINO_001', _('Minor Safety Issue')),
        ('OTHE_001', _('Other Violation')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name=_('Related report')
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='moderation_actions',
        verbose_name=_('Moderator')
    )
    action_type = models.CharField(_('Action type'), max_length=20, choices=ACTION_TYPE_CHOICES)
    reason_code = models.CharField(_('Reason code'), max_length=10, choices=REASON_CODE_CHOICES)
    reason_text = models.TextField(_('Detailed reason'))
    
    # Target details
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='moderation_actions_received',
        null=True,
        blank=True,
        verbose_name=_('Target user')
    )
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target_content = GenericForeignKey('content_type', 'object_id')
    
    # Action details
    expires_at = models.DateTimeField(_('Action expires at'), null=True, blank=True)
    is_permanent = models.BooleanField(_('Permanent action'), default=False)
    
    # Internal tracking
    internal_notes = models.TextField(_('Internal notes'), blank=True)
    ip_address = models.GenericIPAddressField(_('IP address'))
    user_agent = models.TextField(_('User agent'), blank=True)

    class Meta:
        verbose_name = _('Moderation Action')
        verbose_name_plural = _('Moderation Actions')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_type_display()} by {self.moderator.full_name}"

    @property
    def is_active(self):
        if self.is_permanent:
            return True
        if self.expires_at:
            return timezone.now() < self.expires_at
        return True


class Appeal(BaseModel):
    """
    User appeals for moderation actions.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('under_review', _('Under Review')),
        ('approved', _('Appeal Approved')),
        ('denied', _('Appeal Denied')),
        ('escalated', _('Escalated')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    moderation_action = models.ForeignKey(
        ModerationAction,
        on_delete=models.CASCADE,
        related_name='appeals'
    )
    appellant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='appeals_submitted'
    )
    
    # Appeal content
    appeal_text = models.TextField(_('Appeal explanation'))
    additional_evidence = models.FileField(
        _('Additional evidence'),
        upload_to='appeals/evidence/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    
    # Status and resolution
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appeals_reviewed'
    )
    reviewed_at = models.DateTimeField(_('Reviewed at'), null=True, blank=True)
    resolution_notes = models.TextField(_('Resolution notes'), blank=True)
    
    # SLA tracking
    sla_due_at = models.DateTimeField(_('SLA due at'))

    class Meta:
        verbose_name = _('Appeal')
        verbose_name_plural = _('Appeals')
        ordering = ['sla_due_at', '-created_at']

    def __str__(self):
        return f"Appeal #{self.id.hex[:8]} by {self.appellant.full_name}"

    def save(self, *args, **kwargs):
        if not self.sla_due_at:
            # Appeals have 72-hour SLA
            self.sla_due_at = self.created_at + timedelta(hours=72)
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return timezone.now() > self.sla_due_at


class ModerationTemplate(BaseModel):
    """
    Canned responses and templates for moderators.
    """
    TEMPLATE_TYPE_CHOICES = [
        ('warning', _('Warning Message')),
        ('rejection', _('Rejection Notice')),
        ('suspension', _('Suspension Notice')),
        ('appeal_response', _('Appeal Response')),
        ('policy_reminder', _('Policy Reminder')),
    ]

    name = models.CharField(_('Template name'), max_length=100)
    template_type = models.CharField(_('Template type'), max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    reason_codes = models.JSONField(_('Applicable reason codes'), default=list)
    
    # Localized content
    subject_ar = models.CharField(_('Arabic subject'), max_length=200)
    subject_en = models.CharField(_('English subject'), max_length=200)
    content_ar = models.TextField(_('Arabic content'))
    content_en = models.TextField(_('English content'))
    
    # Template variables
    variables = models.JSONField(_('Template variables'), default=list)
    is_active = models.BooleanField(_('Active'), default=True)
    usage_count = models.PositiveIntegerField(_('Usage count'), default=0)

    class Meta:
        verbose_name = _('Moderation Template')
        verbose_name_plural = _('Moderation Templates')
        ordering = ['template_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class UserSuspension(BaseModel):
    """
    Enhanced user suspensions with appeals support.
    """
    SUSPENSION_TYPE_CHOICES = [
        ('temporary', _('Temporary Suspension')),
        ('permanent', _('Permanent Ban')),
        ('shadow', _('Shadow Ban')),
        ('feature_restriction', _('Feature Restriction')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='suspensions',
        verbose_name=_('User')
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='suspensions_issued',
        verbose_name=_('Moderator')
    )
    moderation_action = models.ForeignKey(
        ModerationAction,
        on_delete=models.CASCADE,
        related_name='suspensions'
    )
    
    # Suspension details
    suspension_type = models.CharField(_('Suspension type'), max_length=20, choices=SUSPENSION_TYPE_CHOICES)
    reason_code = models.CharField(_('Reason code'), max_length=10, choices=ModerationAction.REASON_CODE_CHOICES)
    reason_text = models.TextField(_('Reason'))
    
    # Duration
    expires_at = models.DateTimeField(_('Expires at'), null=True, blank=True)
    is_permanent = models.BooleanField(_('Permanent'), default=False)
    
    # Restrictions
    restricted_features = models.JSONField(_('Restricted features'), default=list)
    
    # Appeal tracking
    can_appeal = models.BooleanField(_('Can appeal'), default=True)
    appeal_deadline = models.DateTimeField(_('Appeal deadline'), null=True, blank=True)

    class Meta:
        verbose_name = _('User Suspension')
        verbose_name_plural = _('User Suspensions')
        ordering = ['-created_at']

    def __str__(self):
        return f"Suspension of {self.user.full_name}"

    def save(self, *args, **kwargs):
        if not self.appeal_deadline and self.can_appeal:
            # Users have 30 days to appeal
            self.appeal_deadline = self.created_at + timedelta(days=30)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        if self.is_permanent:
            return True
        if self.expires_at:
            return timezone.now() < self.expires_at
        return False

    @property
    def can_still_appeal(self):
        return (
            self.can_appeal and 
            self.appeal_deadline and 
            timezone.now() < self.appeal_deadline and
            not self.appeals.filter(status__in=['pending', 'under_review']).exists()
        )


class ModerationQueue(BaseModel):
    """
    Queue management for moderation workflow.
    """
    QUEUE_TYPE_CHOICES = [
        ('reports', _('Reports Queue')),
        ('appeals', _('Appeals Queue')),
        ('escalations', _('Escalations Queue')),
        ('policy_violations', _('Policy Violations')),
    ]

    queue_type = models.CharField(_('Queue type'), max_length=20, choices=QUEUE_TYPE_CHOICES)
    priority = models.PositiveIntegerField(_('Priority'), default=50)
    
    # Assignment
    assigned_moderators = models.ManyToManyField(
        User,
        related_name='moderation_queues',
        blank=True
    )
    auto_assign = models.BooleanField(_('Auto assign'), default=True)
    
    # SLA configuration
    sla_hours = models.PositiveIntegerField(_('SLA hours'), default=24)
    escalation_hours = models.PositiveIntegerField(_('Escalation hours'), default=48)
    
    # Queue settings
    is_active = models.BooleanField(_('Active'), default=True)
    max_concurrent_items = models.PositiveIntegerField(_('Max concurrent items'), default=10)

    class Meta:
        verbose_name = _('Moderation Queue')
        verbose_name_plural = _('Moderation Queues')
        ordering = ['priority', 'queue_type']

    def __str__(self):
        return f"{self.get_queue_type_display()} Queue"


class PolicyAcknowledgment(BaseModel):
    """
    Track user acknowledgment of policy versions.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='policy_acknowledgments'
    )
    policy_version = models.ForeignKey(
        PolicyVersion,
        on_delete=models.CASCADE,
        related_name='acknowledgments'
    )
    acknowledged_at = models.DateTimeField(_('Acknowledged at'), default=timezone.now)
    ip_address = models.GenericIPAddressField(_('IP address'))
    user_agent = models.TextField(_('User agent'), blank=True)

    class Meta:
        verbose_name = _('Policy Acknowledgment')
        verbose_name_plural = _('Policy Acknowledgments')
        unique_together = ['user', 'policy_version']
        ordering = ['-acknowledged_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.policy_version}"


class AutoModerationRule(BaseModel):
    """
    Automated moderation rules and triggers.
    """
    TRIGGER_TYPE_CHOICES = [
        ('keyword', _('Keyword Match')),
        ('pattern', _('Pattern Match')),
        ('frequency', _('Frequency Threshold')),
        ('reputation', _('Reputation Score')),
        ('ml_confidence', _('ML Confidence Score')),
    ]
    
    ACTION_TYPE_CHOICES = [
        ('flag', _('Flag for Review')),
        ('auto_hide', _('Auto Hide')),
        ('auto_reject', _('Auto Reject')),
        ('require_review', _('Require Manual Review')),
        ('rate_limit', _('Apply Rate Limit')),
    ]

    name = models.CharField(_('Rule name'), max_length=100)
    description = models.TextField(_('Description'))
    trigger_type = models.CharField(_('Trigger type'), max_length=15, choices=TRIGGER_TYPE_CHOICES)
    trigger_config = models.JSONField(_('Trigger configuration'))
    
    # Actions
    action_type = models.CharField(_('Action type'), max_length=15, choices=ACTION_TYPE_CHOICES)
    action_config = models.JSONField(_('Action configuration'), default=dict)
    
    # Targeting
    target_content_types = models.ManyToManyField(ContentType, blank=True)
    severity = models.CharField(_('Severity'), max_length=10, choices=Report.SEVERITY_CHOICES, default='medium')
    
    # Performance
    is_active = models.BooleanField(_('Active'), default=True)
    trigger_count = models.PositiveIntegerField(_('Trigger count'), default=0)
    false_positive_count = models.PositiveIntegerField(_('False positives'), default=0)
    
    # Thresholds
    confidence_threshold = models.FloatField(_('Confidence threshold'), default=0.8)
    review_threshold = models.FloatField(_('Review threshold'), default=0.6)

    class Meta:
        verbose_name = _('Auto Moderation Rule')
        verbose_name_plural = _('Auto Moderation Rules')
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def accuracy_rate(self):
        total = self.trigger_count
        if total == 0:
            return 0
        return ((total - self.false_positive_count) / total) * 100