"""
Management command to create a superuser for the Egyptian Service Marketplace.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from phonenumber_field.phonenumber import PhoneNumber

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser for the marketplace'

    def add_arguments(self, parser):
        parser.add_argument('--phone', type=str, help='Phone number for the superuser')
        parser.add_argument('--name', type=str, help='Full name for the superuser')
        parser.add_argument('--password', type=str, help='Password for the superuser')

    def handle(self, *args, **options):
        phone = options.get('phone') or '+201000000000'
        name = options.get('name') or 'مدير النظام'
        password = options.get('password') or 'admin123456'

        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING('Superuser already exists!')
            )
            return

        try:
            # Create superuser
            user = User.objects.create_superuser(
                phone_number=PhoneNumber.from_string(phone, region='EG'),
                full_name=name,
                password=password,
                email='admin@marketplace.eg'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {user.full_name} ({user.phone_number})')
            )
            self.stdout.write(f'Login credentials:')
            self.stdout.write(f'  Phone: {phone}')
            self.stdout.write(f'  Password: {password}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )