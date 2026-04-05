import os
import django
import random
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings.dev')
if not settings.configured:
    django.setup()

from django.contrib.auth import get_user_model
from apps.services.models import ServiceCategory, ServiceSubcategory, Service, ServiceImage
from apps.core.models import Province, City

User = get_user_model()

def create_locations():
    print("Creating Locations...")
    govs = [
        {"name_ar": "القاهرة", "name_en": "Cairo", "code": "CAI"},
        {"name_ar": "الجيزة", "name_en": "Giza", "code": "GZ"},
        {"name_ar": "الإسكندرية", "name_en": "Alexandria", "code": "ALX"},
    ]
    
    created_govs = []
    for gov_data in govs:
        gov, created = Province.objects.get_or_create(
            code=gov_data['code'],
            defaults=gov_data
        )
        created_govs.append(gov)
        
        # Add some cities
        cities = [f"{gov_data['name_en']} City 1", f"{gov_data['name_en']} City 2"]
        for i, city_name in enumerate(cities):
            City.objects.get_or_create(
                province=gov,
                name_en=city_name,
                defaults={"name_ar": f"مدينة {gov_data['name_ar']} {i+1}"}
            )
    return created_govs

def create_categories():
    print("Creating Categories...")
    categories_data = [
        {
            "name_ar": "صيانة منزلية", "name_en": "Home Maintenance", "slug": "home-maintenance",
            "icon": "Hammer", "color": "#FF5733",
            "subs": ["سباكة", "كهرباء", "نجارة", "تكييف"]
        },
        {
            "name_ar": "تكنولوجيا", "name_en": "Technology", "slug": "technology",
            "icon": "Laptop", "color": "#33FF57",
            "subs": ["برمجة", "شبكات", "تطوير مواقع", "صيانة كمبيوتر"]
        },
        {
            "name_ar": "تعليم", "name_en": "Education", "slug": "education",
            "icon": "Book", "color": "#3357FF",
            "subs": ["دروس خصوصية", "لغات", "برمجة للصغار"]
        },
    ]

    created_cats = []
    for cat_data in categories_data:
        subs = cat_data.pop('subs')
        cat, created = ServiceCategory.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        created_cats.append(cat)
        
        for i, sub_name in enumerate(subs):
            ServiceSubcategory.objects.get_or_create(
                category=cat,
                slug=f"{cat.slug}-sub-{i}",
                defaults={
                    "name_ar": sub_name,
                    "name_en": f"{cat_data['name_en']} - {sub_name}",
                    "description_ar": f"خدمات {sub_name}",
                    "description_en": f"{sub_name} services"
                }
            )
    return created_cats

def create_users(count=5):
    print(f"Creating {count} Users...")
    users = []
    for i in range(count):
        phone = f"+2010{i:08d}"
        if not User.objects.filter(phone_number=phone).exists():
            user = User.objects.create_user(
                phone_number=phone,
                password="password123",
                full_name=f"User {i+1}",
                role='user',  # Changed from user_type to role
                status='verified' if i % 2 == 0 else 'pending'
            )
            # Verify phone for verified users
            if user.status == 'verified':
                user.is_phone_verified = True
                user.save()
            users.append(user)
        else:
            users.append(User.objects.get(phone_number=phone))
    return users

def create_services(users, categories):
    print("Creating Services...")
    
    # All users can be providers in this system
    providers = users
    
    cities = list(City.objects.all())
    if not cities:
        print("No cities found, skipping service creation.")
        return

    for i in range(20):
        provider = random.choice(providers) if providers else users[0]
        category = random.choice(categories)
        subcategories = list(category.subcategories.all())
        subcategory = random.choice(subcategories) if subcategories else None
        city = random.choice(cities)
        
        title_ar = f"خدمة {subcategory.name_ar if subcategory else category.name_ar} {i+1}"
        
        service, created = Service.objects.get_or_create(
            slug=f"service-{i+1}",
            defaults={
                "owner": provider,
                "title_ar": title_ar,
                "title_en": f"Service {i+1}",
                "description_ar": "وصف تجريبي للخدمة يحتوي على تفاصيل مميزة.",
                "description_en": "Test service description with details.",
                "category": category,
                "subcategory": subcategory,
                "price": random.randint(100, 5000),
                "currency": "EGP",
                "governorate": city.province,
                "center": city,
                "status": random.choice(['approved', 'pending', 'rejected']),
                "views_count": random.randint(0, 500)
            }
        )
        if created:
            print(f"Created Service: {service.title_en}")

def run():
    print("Starting database population...")
    create_locations()
    cats = create_categories()
    users = create_users(10)
    create_services(users, cats)
    print("Database population completed successfully!")
    print("\nTest Credentials:")
    print("Phone: +201000000000 (User 1) -> Password: password123")
    print("Phone: +201000000001 (User 2) -> Password: password123")

if __name__ == "__main__":
    run()
