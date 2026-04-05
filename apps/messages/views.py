"""
Views for the messages app.
"""

from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Conversation, Message, MessageReport
from .serializers import ConversationSerializer, MessageSerializer, MessageReportSerializer
from apps.accounts.models import AdminAction
from apps.notifications.utils import send_notification_if_enabled


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            Q(customer=user) | Q(provider=user)
        ).distinct()

    def create(self, request, *args, **kwargs):
        service_id = request.data.get('service')
        provider_id = request.data.get('provider')
        initial_message = request.data.get('initial_message')
        
        if not service_id or not provider_id:
            return Response({'error': 'service and provider are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        from apps.services.models import Service
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            service = Service.objects.get(id=service_id)
            provider = User.objects.get(id=provider_id)
        except (Service.DoesNotExist, User.DoesNotExist):
            return Response({'error': 'Invalid service or provider'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get or create
        conversation, created = Conversation.objects.get_or_create(
            service=service,
            customer=request.user,
            provider=provider,
            defaults={'subject': service.title_ar}
        )
        
        if initial_message and created:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=initial_message,
                message_type='text'
            )
            
            # Notify recipient of the initial message
            send_notification_if_enabled(
                recipient=provider,
                notification_type='message',
                title_ar='رسالة جديدة',
                title_en='New Message',
                message_ar=f'تلقيت رسالة جديدة من {request.user.full_name}.',
                message_en=f'You received a new message from {request.user.full_name}.',
                related_object=conversation
            )
            
        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archive a conversation.
        """
        conversation = self.get_object()
        conversation.is_archived = True
        conversation.save()
        return Response({'status': 'archived'})

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """
        Unarchive a conversation.
        """
        conversation = self.get_object()
        conversation.is_archived = False
        conversation.save()
        return Response({'status': 'unarchived'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark all messages in conversation as read for current user.
        """
        conversation = self.get_object()
        user = request.user
        
        # Mark messages as read for the current user
        if user == conversation.customer:
            # Customer reading provider's messages
            messages_to_update = conversation.messages.filter(
                sender=conversation.provider,
                is_read=False
            )
        else:
            # Provider reading customer's messages
            messages_to_update = conversation.messages.filter(
                sender=conversation.customer,
                is_read=False
            )
        
        messages_to_update.update(is_read=True)
        
        return Response({
            'marked_read_count': messages_to_update.count()
        })
    
    @action(detail=True, methods=['post'])
    def start_typing(self, request, pk=None):
        """
        Indicate user is typing.
        """
        conversation = self.get_object()
        user = request.user
        
        # Update typing status
        from django.utils import timezone
        Message.objects.filter(
            conversation=conversation,
            sender=user,
            is_typing=True
        ).update(is_typing=False)
        
        # Create typing indicator (temporary message)
        typing_message = Message.objects.create(
            conversation=conversation,
            sender=user,
            content='',
            message_type='system',
            is_typing=True,
            typing_updated_at=timezone.now()
        )
        
        return Response({'typing_message_id': typing_message.id})
    
    @action(detail=True, methods=['post'])
    def stop_typing(self, request, pk=None):
        """
        Stop typing indicator.
        """
        conversation = self.get_object()
        user = request.user
        
        Message.objects.filter(
            conversation=conversation,
            sender=user,
            is_typing=True
        ).delete()
        
        return Response({'status': 'stopped_typing'})

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get paginated messages for a conversation.
        """
        conversation = self.get_object()
        
        # Ensure user is part of the conversation
        if request.user != conversation.customer and request.user != conversation.provider:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to view these messages.")
            
        messages = conversation.messages.filter(is_active=True).order_by('-created_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)



class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for messages.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(conversation__customer=user) | Q(conversation__provider=user),
            is_active=True
        )

    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)
        
        # Notify the other participant
        conversation = message.conversation
        recipient = conversation.provider if self.request.user == conversation.customer else conversation.customer
        
        send_notification_if_enabled(
            recipient=recipient,
            notification_type='message',
            title_ar='رسالة جديدة',
            title_en='New Message',
            message_ar=f'تلقيت رسالة جديدة من {self.request.user.full_name}.',
            message_en=f'You received a new message from {self.request.user.full_name}.',
            related_object=conversation
        )
    
    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        """
        Report a message.
        """
        message = self.get_object()
        
        # Check if user already reported this message
        if MessageReport.objects.filter(message=message, reporter=request.user).exists():
            return Response(
                {'error': 'You have already reported this message'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MessageReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        report = serializer.save(
            message=message,
            reporter=request.user
        )
        
        return Response({
            'message': 'Message reported successfully',
            'report_id': report.id
        })