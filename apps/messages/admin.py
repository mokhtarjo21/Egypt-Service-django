"""
Admin configuration for messages app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """
    Admin interface for Conversation model.
    """
    list_display = ('subject', 'customer', 'provider', 'service', 'last_message_at', 'is_archived')
    list_filter = ('is_archived', 'created_at', 'last_message_at')
    search_fields = ('subject', 'customer__first_name', 'customer__last_name', 
                    'provider__first_name', 'provider__last_name')
    raw_id_fields = ('service', 'customer', 'provider')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin interface for Message model.
    """
    list_display = ('conversation', 'sender', 'message_type', 'content_preview', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read', 'created_at')
    search_fields = ('conversation__subject', 'sender__first_name', 'sender__last_name', 'content')
    raw_id_fields = ('conversation', 'sender')

    def content_preview(self, obj):
        return obj.content[:100] if obj.content else ''
    content_preview.short_description = 'Content Preview'