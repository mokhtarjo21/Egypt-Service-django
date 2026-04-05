"""
Views for the moderation app.
"""

from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import Report, ModerationAction, Appeal, PolicyVersion, ModerationTemplate
from .serializers import (
    ReportSerializer, 
    ModerationActionSerializer, 
    AppealSerializer,
    PolicyVersionSerializer,
    ModerationTemplateSerializer
)
from apps.accounts.models import AdminAction,User
from apps.notifications.models import Notification


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for reports with triage and assignment.
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Report.objects.all()
        return Report.objects.filter(reporter=user)

    @method_decorator(ratelimit(key='user', rate='5/h', method='POST'))
    def create(self, request, *args, **kwargs):
        """Create a new report with automatic triage."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Auto-assign severity based on reason
        severity_mapping = {
            'violence': 'critical',
            'hate_speech': 'critical',
            'minor_safety': 'critical',
            'fraud': 'high',
            'harassment': 'high',
            'fake': 'high',
            'inappropriate': 'medium',
            'spam': 'low',
            'other': 'medium',
        }
        
        reason = serializer.validated_data['reason']
        severity = severity_mapping.get(reason, 'medium')
        
        report = serializer.save(
            reporter=request.user,
            severity=severity
        )
        
        # Auto-assign to available moderator if critical/high
        if severity in ['critical', 'high']:
            available_moderator = User.objects.filter(
                role='admin',
                reports_assigned__status__in=['pending', 'assigned']
            ).annotate(
                active_reports=Count('reports_assigned')
            ).order_by('active_reports').first()
            
            if available_moderator:
                report.assigned_to = available_moderator
                report.status = 'assigned'
                report.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def triage(self, request, pk=None):
        """Triage a report (admin only)."""
        if not request.user.role == 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        report = self.get_object()
        new_severity = request.data.get('severity')
        assigned_to_id = request.data.get('assigned_to')
        notes = request.data.get('notes', '')
        
        if new_severity:
            report.severity = new_severity
        
        if assigned_to_id:
            try:
                moderator = User.objects.get(id=assigned_to_id, role='admin')
                report.assigned_to = moderator
                report.status = 'assigned'
            except User.DoesNotExist:
                return Response({'error': 'Invalid moderator'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not report.first_response_at:
            report.first_response_at = timezone.now()
        
        report.internal_notes = notes
        report.save()
        
        return Response({
            'message': 'Report triaged successfully',
            'report': ReportSerializer(report).data
        })

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a report with moderation action."""
        if not request.user.role == 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        report = self.get_object()
        action_type = request.data.get('action_type')
        reason_code = request.data.get('reason_code')
        reason_text = request.data.get('reason_text', '')
        
        # Create moderation action
        moderation_action = ModerationAction.objects.create(
            report=report,
            moderator=request.user,
            action_type=action_type,
            reason_code=reason_code,
            reason_text=reason_text,
            target_user=getattr(report.reported_object, 'owner', None) or 
                       (report.reported_object if hasattr(report.reported_object, 'full_name') else None),
            content_type=report.content_type,
            object_id=report.object_id,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Update report status
        report.status = 'resolved'
        report.resolved_at = timezone.now()
        report.resolved_by = request.user
        report.resolution_notes = reason_text
        report.save()
        
        # Execute the moderation action
        self._execute_moderation_action(moderation_action)
        
        # Send notification to affected user
        if moderation_action.target_user:
            Notification.objects.create(
                recipient=moderation_action.target_user,
                notification_type='moderation_action',
                title_ar=f'إجراء إداري: {moderation_action.get_action_type_display()}',
                title_en=f'Moderation Action: {moderation_action.get_action_type_display()}',
                message_ar=reason_text,
                message_en=reason_text,
            )
        
        return Response({
            'message': 'Report resolved successfully',
            'action': ModerationActionSerializer(moderation_action).data
        })

    def _execute_moderation_action(self, action):
        """Execute the actual moderation action."""
        if action.action_type == 'hide_content':
            # Hide the content
            if hasattr(action.target_content, 'is_active'):
                action.target_content.is_active = False
                action.target_content.save()
        
        elif action.action_type == 'suspend_user':
            # Suspend the user
            if action.target_user:
                action.target_user.status = 'suspended'
                action.target_user.save()
        
        elif action.action_type == 'block_user':
            # Block the user
            if action.target_user:
                action.target_user.status = 'blocked'
                action.target_user.save()
        
        elif action.action_type == 'reject_content':
            # Reject content (e.g., service)
            if hasattr(action.target_content, 'status'):
                action.target_content.status = 'rejected'
                action.target_content.rejection_reason = action.reason_text
                action.target_content.save()


class AppealViewSet(viewsets.ModelViewSet):
    """
    ViewSet for appeals.
    """
    serializer_class = AppealSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Appeal.objects.all()
        return Appeal.objects.filter(appellant=user)

    def perform_create(self, serializer):
        serializer.save(appellant=self.request.user)

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Review an appeal (admin only)."""
        if not request.user.role == 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        appeal = self.get_object()
        decision = request.data.get('decision')  # 'approved' or 'denied'
        notes = request.data.get('notes', '')
        
        if decision not in ['approved', 'denied']:
            return Response({'error': 'Invalid decision'}, status=status.HTTP_400_BAD_REQUEST)
        
        appeal.status = decision
        appeal.reviewed_by = request.user
        appeal.reviewed_at = timezone.now()
        appeal.resolution_notes = notes
        appeal.save()
        
        # If appeal approved, reverse the moderation action
        if decision == 'approved':
            moderation_action = appeal.moderation_action
            self._reverse_moderation_action(moderation_action)
        
        # Notify user of appeal decision
        Notification.objects.create(
            recipient=appeal.appellant,
            notification_type='appeal_decision',
            title_ar=f'قرار الاستئناف: {decision}',
            title_en=f'Appeal Decision: {decision}',
            message_ar=notes,
            message_en=notes,
        )
        
        return Response({
            'message': f'Appeal {decision} successfully',
            'appeal': AppealSerializer(appeal).data
        })

    def _reverse_moderation_action(self, action):
        """Reverse a moderation action after successful appeal."""
        if action.action_type == 'hide_content':
            if hasattr(action.target_content, 'is_active'):
                action.target_content.is_active = True
                action.target_content.save()
        
        elif action.action_type in ['suspend_user', 'block_user']:
            if action.target_user:
                action.target_user.status = 'verified'
                action.target_user.save()
        
        elif action.action_type == 'reject_content':
            if hasattr(action.target_content, 'status'):
                action.target_content.status = 'pending'
                action.target_content.rejection_reason = ''
                action.target_content.save()


class PolicyVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for policy versions.
    """
    queryset = PolicyVersion.objects.filter(is_active=True)
    serializer_class = PolicyVersionSerializer
    permission_classes = []  # Public access

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current active policies."""
        policies = {}
        for policy_type, _ in PolicyVersion.POLICY_TYPE_CHOICES:
            policy = PolicyVersion.objects.filter(
                policy_type=policy_type,
                is_active=True
            ).first()
            if policy:
                policies[policy_type] = PolicyVersionSerializer(policy).data
        
        return Response(policies)


class ModerationTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for moderation templates (admin only).
    """
    queryset = ModerationTemplate.objects.filter(is_active=True)
    serializer_class = ModerationTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.role == 'admin':
            return ModerationTemplate.objects.none()
        return super().get_queryset()

    @action(detail=False, methods=['get'])
    def by_reason(self, request):
        """Get templates by reason code."""
        reason_code = request.query_params.get('reason_code')
        if not reason_code:
            return Response({'error': 'reason_code required'}, status=status.HTTP_400_BAD_REQUEST)
        
        templates = self.get_queryset().filter(
            reason_codes__contains=[reason_code]
        )
        
        return Response(self.get_serializer(templates, many=True).data)


class ModerationDashboardView(generics.GenericAPIView):
    """
    Admin moderation dashboard with queue statistics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.role == 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Queue statistics
        queue_stats = {
            'pending_reports': Report.objects.filter(status='pending').count(),
            'assigned_reports': Report.objects.filter(status='assigned').count(),
            'overdue_reports': Report.objects.filter(
                sla_due_at__lt=timezone.now(),
                status__in=['pending', 'assigned', 'investigating']
            ).count(),
            'pending_appeals': Appeal.objects.filter(status='pending').count(),
            'overdue_appeals': Appeal.objects.filter(
                sla_due_at__lt=timezone.now(),
                status__in=['pending', 'under_review']
            ).count(),
        }
        
        # Recent activity
        recent_reports = Report.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        recent_actions = ModerationAction.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        # Moderator workload
        moderator_workload = User.objects.filter(
            role='admin'
        ).annotate(
            active_reports=Count('reports_assigned', filter=Q(reports_assigned__status__in=['assigned', 'investigating']))
        ).values('id', 'full_name', 'active_reports')
        
        return Response({
            'queue_stats': queue_stats,
            'recent_reports': ReportSerializer(recent_reports, many=True).data,
            'recent_actions': ModerationActionSerializer(recent_actions, many=True).data,
            'moderator_workload': list(moderator_workload),
        })