import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings.dev')
# Configure settings if not already configured
if not settings.configured:
    django.setup()
else:
    # If already configured (e.g. by some other import), just ensure setup
    try:
        django.setup()
    except Exception:
        pass

from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_user():
    phone_number = "+201126330581"
    password = "123123"
    email = "test@example.com"
    full_name = "Test User"
    
    if User.objects.filter(phone_number=phone_number).exists():
        print(f"User {phone_number} already exists.")
        user = User.objects.get(phone_number=phone_number)
        user.set_password(password)
        user.is_active = True
        user.is_phone_verified = True
        user.status = 'verified'
        user.save()
        print(f"Updated password to '{password}' and verified status.")
    else:
        print(f"Creating user {phone_number}...")
        user = User.objects.create_user(
            phone_number=phone_number,
            password=password,
            email=email,
            full_name=full_name,
            is_active=True,
            is_phone_verified=True,
            status='verified',
            role='user'
        )
        print(f"User created successfully.")

    print(f"\nCredentials:")
    print(f"Phone Number: {phone_number}")
    print(f"Password: {password}")

if __name__ == "__main__":
    create_test_user()
