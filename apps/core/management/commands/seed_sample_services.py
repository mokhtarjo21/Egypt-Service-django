"""
Management command to seed sample services for testing.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from phonenumber_field.phonenumber import PhoneNumber

from apps.services.models import ServiceCategory, ServiceSubcategory, Service
from apps.core.models import Province, City

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed sample services for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample users and services...')
        
        # Get or create sample provinces and cities
        cairo, _ = Province.objects.get_or_create(
            code='CAI',
            defaults={'name_ar': 'القاهرة', 'name_en': 'Cairo'}
        )
        
        nasr_city, _ = City.objects.get_or_create(
            province=cairo,
            name_ar='مدينة نصر',
            defaults={'name_en': 'Nasr City'}
        )

        # Get categories
        home_services = ServiceCategory.objects.filter(slug='home-services').first()
        education = ServiceCategory.objects.filter(slug='education-training').first()
        
        if not home_services or not education:
            self.stdout.write(
                self.style.WARNING('Please run seed_service_categories first!')
            )
            return

        # Create sample users
        sample_users = [
            {
                'phone': '+201012345678',
                'name': 'أحمد محمد علي',
                'email': 'ahmed@example.com',
            },
            {
                'phone': '+201098765432', 
                'name': 'فاطمة حسن محمود',
                'email': 'fatma@example.com',
            },
            {
                'phone': '+201123456789',
                'name': 'محمود عبد الرحمن',
                'email': 'mahmoud@example.com',
            }
        ]

        users = []
        for user_data in sample_users:
            user, created = User.objects.get_or_create(
                phone_number=PhoneNumber.from_string(user_data['phone'], region='EG'),
                defaults={
                    'full_name': user_data['name'],
                    'email': user_data['email'],
                    'governorate': cairo,
                    'center': nasr_city,
                    'status': 'verified',
                    'is_phone_verified': True,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {user.full_name}')
            users.append(user)

        # Sample services data
        services_data = [
            {
                'title_ar': 'صيانة أجهزة كهربائية منزلية',
                'title_en': 'Home Electrical Appliance Repair',
                'description_ar': 'خدمة صيانة شاملة لجميع الأجهزة الكهربائية المنزلية مع ضمان على الخدمة لمدة 6 أشهر. نقوم بإصلاح الثلاجات، الغسالات، المكيفات، والأجهزة الصغيرة.',
                'description_en': 'Comprehensive repair service for all home electrical appliances with 6-month service warranty.',
                'category': home_services,
                'price': 150,
                'owner': users[0],
                'duration_minutes': 120,
            },
            {
                'title_ar': 'دروس خصوصية في الرياضيات',
                'title_en': 'Private Mathematics Tutoring',
                'description_ar': 'دروس خصوصية في الرياضيات لجميع المراحل التعليمية من الابتدائي حتى الثانوي. خبرة 10 سنوات في التدريس مع نتائج مضمونة.',
                'description_en': 'Private mathematics tutoring for all educational levels from primary to secondary.',
                'category': education,
                'price': 200,
                'owner': users[1],
                'duration_minutes': 60,
            },
            {
                'title_ar': 'تصميم وتطوير مواقع الويب',
                'title_en': 'Web Design and Development',
                'description_ar': 'تصميم وتطوير مواقع ويب احترافية متجاوبة مع جميع الأجهزة. نستخدم أحدث التقنيات لضمان أفضل أداء وتجربة مستخدم.',
                'description_en': 'Professional responsive web design and development using latest technologies.',
                'category': ServiceCategory.objects.filter(slug='it-technology').first(),
                'price': 500,
                'owner': users[2],
                'duration_minutes': 480,
            },
        ]

        # Create services
        for service_data in services_data:
            if not service_data['category']:
                continue
                
            # Get first subcategory for the category
            subcategory = service_data['category'].subcategories.first()
            if not subcategory:
                continue

            service, created = Service.objects.get_or_create(
                slug=slugify(service_data['title_en']),
                defaults={
                    'title_ar': service_data['title_ar'],
                    'title_en': service_data['title_en'],
                    'description_ar': service_data['description_ar'],
                    'description_en': service_data['description_en'],
                    'category': service_data['category'],
                    'subcategory': subcategory,
                    'owner': service_data['owner'],
                    'price': service_data['price'],
                    'duration_minutes': service_data['duration_minutes'],
                    'governorate': cairo,
                    'center': nasr_city,
                    'status': 'approved',
                    'is_on_site': True,
                    'is_online': False,
                }
            )
            
            if created:
                self.stdout.write(f'Created service: {service.title_ar}')

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded sample services!')
        )