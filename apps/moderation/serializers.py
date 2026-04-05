"""
Serializers for the moderation app.
"""

from rest_framework import serializers
from .models import Report, ModerationAction, Appeal, PolicyVersion, ModerationTemplate
from apps.accounts.serializers import UserSerializer


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer for Report model.
    """
    reporter = UserSerializer(read_only=True)
    time_to_sla = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reason', 'description', 'evidence', 'content_type',
            'object_id', 'severity', 'status', 'assigned_to', 'sla_due_at',
            'first_response_at', 'resolved_at', 'resolution_notes', 'internal_notes',
            'time_to_sla', 'is_overdue', 'created_at'
        ]
        read_only_fields = ['reporter', 'severity', 'status', 'assigned_to', 'sla_due_at']


class ModerationActionSerializer(serializers.ModelSerializer):
    """
    Serializer for ModerationAction model.
    """
    moderator = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = ModerationAction
        fields = [
            'id', 'report', 'moderator', 'action_type', 'reason_code', 'reason_text',
            'target_user', 'content_type', 'object_id', 'expires_at', 'is_permanent',
            'internal_notes', 'is_active', 'created_at'
        ]


class AppealSerializer(serializers.ModelSerializer):
    """
    Serializer for Appeal model.
    """
    appellant = UserSerializer(read_only=True)
    moderation_action = ModerationActionSerializer(read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Appeal
        fields = [
            'id', 'moderation_action', 'appellant', 'appeal_text', 'additional_evidence',
            'status', 'reviewed_by', 'reviewed_at', 'resolution_notes', 'sla_due_at',
            'is_overdue', 'created_at'
        ]
        read_only_fields = ['appellant', 'reviewed_by', 'reviewed_at', 'sla_due_at']


class PolicyVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for PolicyVersion model.
    """
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = PolicyVersion
        fields = [
            'id', 'policy_type', 'version', 'title_ar', 'title_en',
            'content_ar', 'content_en', 'is_active', 'effective_date',
            'created_by', 'change_summary', 'created_at'
        ]


class ModerationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for ModerationTemplate model.
    """
    class Meta:
        model = ModerationTemplate
        fields = [
            'id', 'name', 'template_type', 'reason_codes', 'subject_ar',
            'subject_en', 'content_ar', 'content_en', 'variables', 'usage_count'
        ]