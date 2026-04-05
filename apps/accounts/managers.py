"""
Custom managers for the accounts app.
"""

from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from phonenumber_field.phonenumber import PhoneNumber


class UserManager(BaseUserManager):
    """
    Custom user manager where phone number is the unique identifier
    for authentication.
    """
    
    def create_user(self, phone_number, full_name, password=None, **extra_fields):
        """
        Create and save a User with the given phone, name and password.
        """
        if not phone_number:
            raise ValueError(_('The Phone number must be set'))
        if not full_name:
            raise ValueError(_('The Full name must be set'))
            
        # Normalize phone number
        if isinstance(phone_number, str):
            phone_number = PhoneNumber.from_string(phone_number, region='EG')
            
        user = self.model(
            phone_number=phone_number,
            full_name=full_name,
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, phone_number, full_name, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given phone, name and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('status', 'verified')
        extra_fields.setdefault('is_phone_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(phone_number, full_name, password, **extra_fields)