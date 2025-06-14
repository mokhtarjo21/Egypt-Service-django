from rest_framework import serializers
from .models import Comment
from django.contrib.auth.models import User
from products.models import Product

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'user', 'product', 'content', 'created_at']
        read_only_fields = ['created_at']