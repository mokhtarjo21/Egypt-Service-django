"""
Management command to seed service categories.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.services.models import ServiceCategory, ServiceSubcategory


class Command(BaseCommand):
    help = 'Seed service categories and subcategories'

    def handle(self, *args, **options):
        self.stdout.write('Seeding service categories...')
        
        categories_data = [
            {
                'name_ar': 'خدمات منزلية',
                'name_en': 'Home Services',
                'icon': 'home',
                'color': '#3B82F6',
                'subcategories': [
                    {'name_ar': 'تنظيف منازل', 'name_en': 'House Cleaning'},
                    {'name_ar': 'صيانة أجهزة', 'name_en': 'Appliance Repair'},
                    {'name_ar': 'سباكة', 'name_en': 'Plumbing'},
                    {'name_ar': 'كهرباء', 'name_en': 'Electrical'},
                    {'name_ar': 'دهانات', 'name_en': 'Painting'},
                ]
            },
            {
                'name_ar': 'تعليم وتدريب',
                'name_en': 'Education & Training',
                'icon': 'book',
                'color': '#14B8A6',
                'subcategories': [
                    {'name_ar': 'دروس خصوصية', 'name_en': 'Private Tutoring'},
                    {'name_ar': 'تعليم لغات', 'name_en': 'Language Learning'},
                    {'name_ar': 'تدريب مهني', 'name_en': 'Professional Training'},
                    {'name_ar': 'موسيقى وفنون', 'name_en': 'Music & Arts'},
                ]
            },
            {
                'name_ar': 'صحة وجمال',
                'name_en': 'Health & Beauty',
                'icon': 'heart',
                'color': '#F97316',
                'subcategories': [
                    {'name_ar': 'تصفيف شعر', 'name_en': 'Hair Styling'},
                    {'name_ar': 'عناية بالبشرة', 'name_en': 'Skincare'},
                    {'name_ar': 'مساج وعلاج طبيعي', 'name_en': 'Massage & Therapy'},
                    {'name_ar': 'تجميل', 'name_en': 'Beauty Services'},
                ]
            },
            {
                'name_ar': 'تقنية ومعلومات',
                'name_en': 'IT & Technology',
                'icon': 'laptop',
                'color': '#8B5CF6',
                'subcategories': [
                    {'name_ar': 'تطوير مواقع', 'name_en': 'Web Development'},
                    {'name_ar': 'تطبيقات موبايل', 'name_en': 'Mobile Apps'},
                    {'name_ar': 'تصميم جرافيك', 'name_en': 'Graphic Design'},
                    {'name_ar': 'دعم تقني', 'name_en': 'Technical Support'},
                ]
            },
            {
                'name_ar': 'أعمال ومال',
                'name_en': 'Business & Finance',
                'icon': 'briefcase',
                'color': '#EF4444',
                'subcategories': [
                    {'name_ar': 'استشارات مالية', 'name_en': 'Financial Consulting'},
                    {'name_ar': 'محاسبة', 'name_en': 'Accounting'},
                    {'name_ar': 'تسويق رقمي', 'name_en': 'Digital Marketing'},
                    {'name_ar': 'إدارة أعمال', 'name_en': 'Business Management'},
                ]
            },
            {
                'name_ar': 'مناسبات وحفلات',
                'name_en': 'Events & Parties',
                'icon': 'calendar',
                'color': '#10B981',
                'subcategories': [
                    {'name_ar': 'تنظيم حفلات', 'name_en': 'Party Planning'},
                    {'name_ar': 'تصوير مناسبات', 'name_en': 'Event Photography'},
                    {'name_ar': 'تجهيز طعام', 'name_en': 'Catering'},
                    {'name_ar': 'ديكور وتنسيق', 'name_en': 'Decoration'},
                ]
            },
        ]

        for cat_data in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                slug=slugify(cat_data['name_en']),
                defaults={
                    'name_ar': cat_data['name_ar'],
                    'name_en': cat_data['name_en'],
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'is_featured': True,
                }
            )
            
            if created:
                self.stdout.write(f'Created category: {category.name_ar}')
            
            # Create subcategories
            for i, subcat_data in enumerate(cat_data['subcategories']):
                subcategory, created = ServiceSubcategory.objects.get_or_create(
                    category=category,
                    slug=slugify(subcat_data['name_en']),
                    defaults={
                        'name_ar': subcat_data['name_ar'],
                        'name_en': subcat_data['name_en'],
                        'sort_order': i,
                    }
                )
                
                if created:
                    self.stdout.write(f'  Created subcategory: {subcategory.name_ar}')

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded service categories!')
        )