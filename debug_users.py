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

def list_users():
    print("Listing users in database:")
    users = User.objects.all()
    if not users.exists():
        print("No users found.")
        return

    print(f"{'ID':<36} | {'Phone Number':<20} | {'Full Name':<20} | {'Active'} | {'Verified'} | {'Status'}")
    print("-" * 120)
    for user in users:
        print(f"{str(user.id):<36} | {str(user.phone_number):<20} | {user.full_name:<20} | {user.is_active:<6} | {user.is_phone_verified:<8} | {user.status}")

if __name__ == "__main__":
    list_users()
