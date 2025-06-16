from django.db import models
from users.models import User

class Service(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=100,)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    governorate = models.CharField(max_length=50, help_text="Service governorate")
    center = models.CharField(max_length=100, help_text="Service center")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending',
        help_text='Status of the service approval process.'
    )
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Services"

class ServiceImage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField()
    createdAt = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.service.title}"
    
    class Meta:
        verbose_name_plural = "Service Images"