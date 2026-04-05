"""
Core models for Egyptian Service Marketplace.
Base models and mixins used across the application.
"""

import json
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import json


class TimeStampedModel(models.Model):
    """
    Abstract base class that provides self-updating created and modified fields.
    """
    created_at = models.DateTimeField(_('Created at'), default=timezone.now)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract base class that provides soft delete functionality.
    """
    is_active = models.BooleanField(_('Is active'), default=True)
    deleted_at = models.DateTimeField(_('Deleted at'), null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        Soft delete the object by setting is_active to False and deleted_at to now.
        """
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        """
        Actually delete the object.
        """
        super().delete(using=using, keep_parents=keep_parents)


class BaseModel(TimeStampedModel, SoftDeleteModel):
    """
    Base model that includes timestamp and soft delete functionality.
    """
    class Meta:
        abstract = True


class Province(models.Model):
    """
    Egyptian provinces/governorates.
    """
    name_ar = models.CharField(_('Arabic name'), max_length=100)
    name_en = models.CharField(_('English name'), max_length=100)
    code = models.CharField(_('Province code'), max_length=10, unique=True)
    
    class Meta:
        verbose_name = _('Province')
        verbose_name_plural = _('Provinces')
        ordering = ['name_ar']

    def __str__(self):
        return self.name_ar


class City(models.Model):
    """
    Cities within provinces.
    """
    province = models.ForeignKey(
        Province, 
        on_delete=models.CASCADE, 
        related_name='cities',
        verbose_name=_('Province')
    )
    name_ar = models.CharField(_('Arabic name'), max_length=100)
    name_en = models.CharField(_('English name'), max_length=100)
    
    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
        ordering = ['name_ar']
        unique_together = ['province', 'name_ar']

    def __str__(self):
        return f"{self.name_ar} - {self.province.name_ar}"


class SystemConfiguration(BaseModel):
    """
    System-wide configuration settings.
    """
    key = models.CharField(_('Configuration key'), max_length=100, unique=True)
    value = models.TextField(_('Configuration value'))
    description = models.TextField(_('Description'), blank=True)
    is_public = models.BooleanField(_('Public'), default=False)
    
    class Meta:
        verbose_name = _('System Configuration')
        verbose_name_plural = _('System Configurations')
        ordering = ['key']

    def __str__(self):
        return self.key
    
    def get_value(self):
        """Parse JSON value if applicable."""
        try:
            return json.loads(self.value)
        except (json.JSONDecodeError, TypeError):
            return self.value
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a configuration value."""
        try:
            config = cls.objects.get(key=key, is_active=True)
            return config.get_value()
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key, value, description=''):
        """Set a configuration value."""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        config, created = cls.objects.get_or_create(
            key=key,
            defaults={'value': str(value), 'description': description}
        )
        
        if not created:
            config.value = str(value)
            config.description = description
            config.save()
        
        return config