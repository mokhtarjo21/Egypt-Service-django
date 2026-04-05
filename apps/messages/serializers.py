"""
Serializers for the messages app.
"""

from rest_framework import serializers
from .models import Conversation, Message, MessageReport
from apps.accounts.serializers import UserSerializer
from apps.services.serializers import ServiceSerializer


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model.
    """
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'message_type', 'content',
            'attachment', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['sender', 'is_read', 'read_at']


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation model.
    """
    service = ServiceSerializer(read_only=True)
    customer = UserSerializer(read_only=True)
    provider = UserSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'service', 'customer', 'provider', 'subject',
            'is_archived', 'last_message_at', 'last_message',
            'unread_count', 'created_at'
        ]

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        request_user = self.context['request'].user
        if request_user == obj.customer:
            return obj.unread_count_for_customer
        elif request_user == obj.provider:
            return obj.unread_count_for_provider
        return 0


class MessageReportSerializer(serializers.ModelSerializer):
    """
    Serializer for MessageReport model.
    """
    class Meta:
        model = MessageReport
        fields = ['reason', 'description']