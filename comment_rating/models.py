from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User
from service.models import Service

from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.core.exceptions import ValidationError  



class Rating(models.Model):
    """
        project ratings 
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='ratings')
    content = models.TextField( null=True, blank=True)
    value = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # composite primay key to add one rating to one project
        unique_together = ('user', 'service')

        
# @receiver(post_save, sender=Rating)
# def update_product_rating(sender, instance, **kwargs):
#     product = instance.product
#     average = product.ratings.aggregate(avg_rating=Avg('value'))['avg_rating'] or 0.0
#     product.rating_average = round(average, 2)
#     product.save()




# Create your models here.
