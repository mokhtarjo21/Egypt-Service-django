"""
Service models for Egyptian Service Marketplace.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericRelation
from apps.core.models import BaseModel, Province, City

User = get_user_model()


class ServiceCategory(BaseModel):
    """
    Service categories (e.g., Home Services, Beauty, Education, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name_ar = models.CharField(_('Arabic name'), max_length=100)
    name_en = models.CharField(_('English name'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    description_ar = models.TextField(_('Arabic description'), blank=True)
    description_en = models.TextField(_('English description'), blank=True)
    icon = models.CharField(_('Icon'), max_length=50, blank=True)
    color = models.CharField(_('Color'), max_length=7, default='#3B82F6')
    is_featured = models.BooleanField(_('Featured'), default=False)
    sort_order = models.PositiveIntegerField(_('Sort order'), default=0)
    
    class Meta:
        verbose_name = _('Service Category')
        verbose_name_plural = _('Service Categories')
        ordering = ['sort_order', 'name_ar']

    def __str__(self):
        return self.name_ar


class ServiceSubcategory(BaseModel):
    """
    Service subcategories within categories.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='subcategories'
    )
    name_ar = models.CharField(_('Arabic name'), max_length=100)
    name_en = models.CharField(_('English name'), max_length=100)
    slug = models.SlugField(_('Slug'))
    description_ar = models.TextField(_('Arabic description'), blank=True)
    description_en = models.TextField(_('English description'), blank=True)
    sort_order = models.PositiveIntegerField(_('Sort order'), default=0)
    
    class Meta:
        verbose_name = _('Service Subcategory')
        verbose_name_plural = _('Service Subcategories')
        ordering = ['sort_order', 'name_ar']
        unique_together = ['category', 'slug']

    def __str__(self):
        return f"{self.category.name_ar} - {self.name_ar}"


class Service(BaseModel):
    """
    Services offered by providers.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending Approval')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('suspended', _('Suspended')),
    ]
    
    PRICING_TYPE_CHOICES = [
        ('fixed', _('Fixed Price')),
        ('hourly', _('Per Hour')),
        ('package', _('Package Deal')),
        ('negotiable', _('Negotiable')),
    ]

    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User,on_delete=models.CASCADE,related_name='services_provided',verbose_name=_('Service Owner'))
    governorate = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services"
    )
    center = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services"
    )
    title_ar = models.CharField(_('Arabic title'), max_length=200)
    title_en = models.CharField(_('English title'), max_length=200, blank=True)
    slug = models.SlugField(_('Slug'), unique=True, blank=True)
    description_ar = models.TextField(_('Arabic description'))
    description_en = models.TextField(_('English description'), blank=True)
    
    # Categorization
    category = models.ForeignKey(ServiceCategory,on_delete=models.CASCADE,related_name='services')
    subcategory = models.ForeignKey(ServiceSubcategory,on_delete=models.CASCADE,related_name='services')
    
    # Pricing
    pricing_type = models.CharField(_('Pricing type'),max_length=12,choices=PRICING_TYPE_CHOICES,default='fixed')
    price = models.DecimalField(_('Base price'),max_digits=10,decimal_places=2,validators=[MinValueValidator(0)])
    currency = models.CharField(_('Currency'), max_length=3, default='EGP')
    
    # Service Details
    duration_minutes = models.PositiveIntegerField(_('Duration (minutes)'),null=True,blank=True)
    max_participants = models.PositiveIntegerField(_('Max participants'),default=1,validators=[MinValueValidator(1)])
    
    # Status & Metrics
    status = models.CharField(_('Status'),max_length=10,choices=STATUS_CHOICES,default='pending')
    rejection_reason = models.TextField(_('Rejection reason'), blank=True)
    views_count = models.PositiveIntegerField(_('Views count'), default=0)
    
    events = GenericRelation('analytics.EventTracking',content_type_field='content_type',object_id_field='object_id',related_query_name='services')
    class Meta:
        verbose_name = _('Service')
        verbose_name_plural = _('Services')
        ordering = ['-created_at']

    def __str__(self):
        return self.title_ar

    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def can_be_published(self):
        """Check if service can be published publicly."""
        # Check subscription limits
        from apps.subscriptions.models import Subscription
        subscription = Subscription.objects.filter(user=self.owner, status='active').first()
        
        if not subscription:
            # Free tier - check service count
            active_services = Service.objects.filter(owner=self.owner, status='approved', is_active=True).count()
            return self.is_approved and self.owner.can_publish_services and active_services < 3
        
        # Check subscription limits
        return (
            self.is_approved and 
            self.owner.can_publish_services and 
            subscription.can_create_service()
        )
    

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            base_slug = slugify(self.title_ar, allow_unicode=True)
            slug = base_slug
            counter = 1

            while Service.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def calculate_rating(self):
        """Calculate average rating from reviews."""
        from apps.reviews.models import Review
        reviews = Review.objects.filter(service=self, status='approved')
        if reviews.exists():
            return reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating']
        return 0.0


class ServiceImage(BaseModel):
    """
    Images for services.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(_('Image'), upload_to='services/gallery/')
    caption_ar = models.CharField(_('Arabic caption'), max_length=200, blank=True)
    caption_en = models.CharField(_('English caption'), max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(_('Sort order'), default=0)
    is_primary = models.BooleanField(_('Primary image'), default=False)
    
    class Meta:
        verbose_name = _('Service Image')
        verbose_name_plural = _('Service Images')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.service.title_ar} - Image {self.sort_order}"


class ServiceAttribute(BaseModel):
    """
    Configurable attributes for services (e.g., "Years of Experience", "Certifications").
    """
    ATTRIBUTE_TYPE_CHOICES = [
        ('text', _('Text')),
        ('number', _('Number')),
        ('boolean', _('Yes/No')),
        ('choice', _('Multiple Choice')),
        ('date', _('Date')),
    ]

    name_ar = models.CharField(_('Arabic name'), max_length=100)
    name_en = models.CharField(_('English name'), max_length=100)
    attribute_type = models.CharField(
        _('Attribute type'),
        max_length=10,
        choices=ATTRIBUTE_TYPE_CHOICES
    )
    is_required = models.BooleanField(_('Required'), default=False)
    sort_order = models.PositiveIntegerField(_('Sort order'), default=0)
    
    class Meta:
        verbose_name = _('Service Attribute')
        verbose_name_plural = _('Service Attributes')
        ordering = ['sort_order', 'name_ar']

    def __str__(self):
        return self.name_ar


class ServiceAttributeValue(BaseModel):
    """
    Values for service attributes.
    """
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='attribute_values'
    )
    attribute = models.ForeignKey(
        ServiceAttribute,
        on_delete=models.CASCADE
    )
    value = models.TextField(_('Value'))
    
    class Meta:
        verbose_name = _('Service Attribute Value')
        verbose_name_plural = _('Service Attribute Values')
        unique_together = ['service', 'attribute']

    def __str__(self):
        return f"{self.service.title_ar} - {self.attribute.name_ar}: {self.value}"