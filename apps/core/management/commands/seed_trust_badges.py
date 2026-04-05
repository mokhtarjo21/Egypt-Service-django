"""
Management command to seed trust badges.
"""

from django.core.management.base import BaseCommand
from apps.trust.models import Badge


class Command(BaseCommand):
    help = 'Seed trust badges'

    def handle(self, *args, **options):
        self.stdout.write('Creating trust badges...')
        
        badges_data = [
            {
                'badge_type': 'verified',
                'name_ar': 'موثق',
                'name_en': 'Verified',
                'description_ar': 'تم التحقق من الهوية والمستندات',
                'description_en': 'Identity and documents verified',
                'icon': 'shield-check',
                'color': '#22C55E',
                'search_boost': 1.2,
                'criteria_config': {
                    'requires_id_verification': True,
                    'requires_phone_verification': True,
                }
            },
            {
                'badge_type': 'top_rated',
                'name_ar': 'الأعلى تقييماً',
                'name_en': 'Top Rated',
                'description_ar': 'متوسط تقييم 4.8+ مع 20+ تقييم في آخر 90 يوم',
                'description_en': 'Average rating 4.8+ with 20+ reviews in last 90 days',
                'icon': 'star',
                'color': '#F59E0B',
                'search_boost': 1.5,
                'criteria_config': {
                    'min_rating': 4.8,
                    'min_reviews': 20,
                    'period_days': 90,
                }
            },
            {
                'badge_type': 'responsive',
                'name_ar': 'سريع الاستجابة',
                'name_en': 'Responsive',
                'description_ar': 'متوسط وقت الاستجابة أقل من 30 دقيقة',
                'description_en': 'Average response time under 30 minutes',
                'icon': 'zap',
                'color': '#3B82F6',
                'search_boost': 1.3,
                'criteria_config': {
                    'max_response_time_minutes': 30,
                    'period_days': 30,
                }
            },
            {
                'badge_type': 'featured',
                'name_ar': 'مميز',
                'name_en': 'Featured',
                'description_ar': 'خدمة مميزة ومدفوعة الترويج',
                'description_en': 'Featured and promoted service',
                'icon': 'trophy',
                'color': '#8B5CF6',
                'search_boost': 2.0,
                'criteria_config': {
                    'requires_payment': True,
                    'manual_assignment': True,
                }
            },
            {
                'badge_type': 'expert',
                'name_ar': 'خبير',
                'name_en': 'Expert',
                'description_ar': 'خبير معتمد في هذا المجال',
                'description_en': 'Certified expert in this field',
                'icon': 'award',
                'color': '#6366F1',
                'search_boost': 1.4,
                'criteria_config': {
                    'min_experience_years': 5,
                    'requires_certification': True,
                }
            },
            {
                'badge_type': 'new_provider',
                'name_ar': 'مقدم جديد',
                'name_en': 'New Provider',
                'description_ar': 'مقدم خدمة جديد على المنصة',
                'description_en': 'New service provider on the platform',
                'icon': 'sparkles',
                'color': '#EC4899',
                'search_boost': 0.9,
                'criteria_config': {
                    'max_days_since_join': 30,
                }
            },
        ]

        for badge_data in badges_data:
            badge, created = Badge.objects.get_or_create(
                badge_type=badge_data['badge_type'],
                defaults=badge_data
            )
            
            if created:
                self.stdout.write(f'Created badge: {badge.name_ar}')

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded trust badges!')
        )