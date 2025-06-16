from django.db import models
from django.contrib.auth.models import AbstractUser
class User(AbstractUser):
    
    fullName = models.CharField(max_length=50)
    password = models.CharField(max_length=256)
    phoneNumber = models.CharField(max_length=50, unique=True)
    serviceType = models.CharField(max_length=50)
    picture = models.ImageField( null=True, blank=True, default='default.jpg')
    idPhotoUrl = models.ImageField( null=True, blank=True, default='id_default.jpg')
    idfPhotoUrl = models.ImageField( null=True, blank=True, default='id_front_default.jpg')
    iduserPhotoUrl = models.ImageField( null=True, blank=True, default='id_user_default.jpg')
    bio = models.CharField(max_length=256)
    isActive = models.BooleanField(default=False)  
    isVerified = models.BooleanField(default=False)
    isPhoneVerified = models.BooleanField(default=False)
    verificationStatus = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending',
        help_text='Status of the user verification process.'
    )
  
   
    

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    def __str__(self):
        return self.fullName
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.phoneNumber
        
            
        super().save(*args, **kwargs)

class User_active(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.CharField(max_length=50)
    time_send = models.DateTimeField(auto_now_add=True)
class governorates(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    governorate = models.CharField(max_length=50)
    def __str__(self):
        return self.governorate
class cities(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=50)
    class Meta:
        unique_together = ('user', 'city')
    
    def __str__(self):
        return self.city