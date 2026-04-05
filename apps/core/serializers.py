"""
Core serializers for Egyptian Service Marketplace.
"""

from rest_framework import serializers
from .models import Province, City


class ProvinceSerializer(serializers.ModelSerializer):
    """
    Serializer for Province model.
    """
    class Meta:
        model = Province
        fields = ['id', 'name_ar', 'name_en', 'code']


class CitySerializer(serializers.ModelSerializer):
    """
    Serializer for City model.
    """
    province = ProvinceSerializer(read_only=True)
    
    class Meta:
        model = City
        fields = ['id', 'name_ar', 'name_en', 'province']