"""
Admin configuration for moderation app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Report, ModerationAction, Appeal, PolicyVersion, ModerationTemplate, UserSuspension


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Admin interface for Report model.
    """
    list_display = ('id_short', 'reporter', 'reason', 'severity', 'status', 'assigned_to', 'is_overdue', 'created_at')
    list_filter = ('reason', 'severity', 'status', 'created_at')
    search_fields = ('reporter__full_name', 'description', 'resolution_notes')
    raw_id_fields = ('reporter', 'assigned_to', 'resolved_by')
    actions = ['assign_to_me', 'mark_resolved', 'escalate_reports']
    
    fieldsets = (
        (_('Report Details'), {
            'fields': ('reporter', 'reason', 'description', 'evidence', 'content_type', 'object_id')
        }),
        (_('Triage'), {
            'fields': ('severity', 'status', 'assigned_to', 'sla_due_at')
        }),
        (_('Resolution'), {
            'fields': ('first_response_at', 'resolved_at', 'resolved_by', 'resolution_notes')
        }),
        (_('Internal'), {
            'fields': ('internal_notes', 'escalation_reason')
        }),
    )

    def id_short(self, obj):
        return obj.id.hex[:8]
    id_short.short_description = 'ID'

    def assign_to_me(self, request, queryset):
        queryset.update(assigned_to=request.user, status='assigned')
        self.message_user(request, f'{queryset.count()} reports assigned to you.')
    assign_to_me.short_description = 'Assign selected reports to me'

    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved', resolved_at=timezone.now(), resolved_by=request.user)
        self.message_user(request, f'{queryset.count()} reports marked as resolved.')
    mark_resolved.short_description = 'Mark selected reports as resolved'

    def escalate_reports(self, request, queryset):
        queryset.update(status='escalated')
        self.message_user(request, f'{queryset.count()} reports escalated.')
    escalate_reports.short_description = 'Escalate selected reports'


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    """
    Admin interface for ModerationAction model.
    """
    list_display = ('id_short', 'action_type', 'reason_code', 'moderator', 'target_user', 'is_active', 'created_at')
    list_filter = ('action_type', 'reason_code', 'is_permanent', 'created_at')
    search_fields = ('moderator__full_name', 'target_user__full_name', 'reason_text')
    raw_id_fields = ('report', 'moderator', 'target_user')
    readonly_fields = ('is_active',)

    def id_short(self, obj):
        return obj.id.hex[:8]
    id_short.short_description = 'ID'


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    """
    Admin interface for Appeal model.
    """
    list_display = ('id_short', 'appellant', 'status', 'is_overdue', 'reviewed_by', 'created_at')
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('appellant__full_name', 'appeal_text', 'resolution_notes')
    raw_id_fields = ('moderation_action', 'appellant', 'reviewed_by')
    actions = ['approve_appeals', 'deny_appeals']

    def id_short(self, obj):
        return obj.id.hex[:8]
    id_short.short_description = 'ID'

    def approve_appeals(self, request, queryset):
        queryset.update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{queryset.count()} appeals approved.')
    approve_appeals.short_description = 'Approve selected appeals'

    def deny_appeals(self, request, queryset):
        queryset.update(
            status='denied',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{queryset.count()} appeals denied.')
    deny_appeals.short_description = 'Deny selected appeals'


@admin.register(PolicyVersion)
class PolicyVersionAdmin(admin.ModelAdmin):
    """
    Admin interface for PolicyVersion model.
    """
    list_display = ('policy_type', 'version', 'title_ar', 'is_active', 'effective_date', 'created_by')
    list_filter = ('policy_type', 'is_active', 'effective_date')
    search_fields = ('title_ar', 'title_en', 'content_ar', 'content_en')
    raw_id_fields = ('created_by', 'previous_version')
    
    fieldsets = (
        (_('Policy Information'), {
            'fields': ('policy_type', 'version', 'title_ar', 'title_en')
        }),
        (_('Content'), {
            'fields': ('content_ar', 'content_en')
        }),
        (_('Versioning'), {
            'fields': ('is_active', 'effective_date', 'previous_version', 'change_summary')
        }),
    )


@admin.register(ModerationTemplate)
class ModerationTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for ModerationTemplate model.
    """
    list_display = ('name', 'template_type', 'usage_count', 'is_active')
    list_filter = ('template_type', 'is_active')
    search_fields = ('name', 'subject_ar', 'subject_en')
    
    fieldsets = (
        (_('Template Information'), {
            'fields': ('name', 'template_type', 'reason_codes')
        }),
        (_('Content'), {
            'fields': ('subject_ar', 'subject_en', 'content_ar', 'content_en')
        }),
        (_('Configuration'), {
            'fields': ('variables', 'is_active', 'usage_count')
        }),
    )


@admin.register(UserSuspension)
class UserSuspensionAdmin(admin.ModelAdmin):
    """
    Admin interface for UserSuspension model.
    """
    list_display = ('user', 'suspension_type', 'moderator', 'is_permanent', 'expires_at', 'can_still_appeal')
    list_filter = ('suspension_type', 'is_permanent', 'can_appeal', 'created_at')
    search_fields = ('user__full_name', 'moderator__full_name', 'reason_text')
    raw_id_fields = ('user', 'moderator', 'moderation_action')

    def can_still_appeal(self, obj):
        return obj.can_still_appeal
    can_still_appeal.boolean = True
    can_still_appeal.short_description = 'Can Appeal'