"""
Management command to seed subscription plans.
"""

from django.core.management.base import BaseCommand
from apps.subscriptions.models import SubscriptionPlan, FeatureFlag


class Command(BaseCommand):
    help = 'Seed subscription plans and feature flags'

    def handle(self, *args, **options):
        self.stdout.write('Creating subscription plans...')
        
        # Free Plan
        free_monthly, created = SubscriptionPlan.objects.get_or_create(
            plan_type='free',
            billing_period='monthly',
            defaults={
                'name_ar': 'مجاني',
                'name_en': 'Free',
                'price': 0,
                'max_services': 3,
                'max_team_members': 1,
                'has_advanced_analytics': False,
                'has_priority_support': False,
                'search_ranking_boost': 1.0,
                'featured_credits_included': 0,
                'description_ar': 'خطة مجانية للبدء',
                'description_en': 'Free plan to get started',
                'features_ar': [
                    'حتى 3 خدمات نشطة',
                    'تحليلات أساسية',
                    'دعم فني عادي',
                    'رسائل غير محدودة'
                ],
                'features_en': [
                    'Up to 3 active services',
                    'Basic analytics',
                    'Standard support',
                    'Unlimited messaging'
                ],
                'sort_order': 1,
            }
        )
        
        # Pro Plan - Monthly
        pro_monthly, created = SubscriptionPlan.objects.get_or_create(
            plan_type='pro',
            billing_period='monthly',
            defaults={
                'name_ar': 'احترافي - شهري',
                'name_en': 'Pro - Monthly',
                'price': 299,
                'max_services': 20,
                'max_team_members': 5,
                'has_advanced_analytics': True,
                'has_priority_support': False,
                'search_ranking_boost': 1.2,
                'featured_credits_included': 5,
                'description_ar': 'للمحترفين والشركات الصغيرة',
                'description_en': 'For professionals and small businesses',
                'features_ar': [
                    'حتى 20 خدمة نشطة',
                    'تحليلات متقدمة',
                    'تعزيز في نتائج البحث',
                    '5 رصيد ترويج شهرياً',
                    'حتى 5 أعضاء فريق'
                ],
                'features_en': [
                    'Up to 20 active services',
                    'Advanced analytics',
                    'Search ranking boost',
                    '5 featured credits monthly',
                    'Up to 5 team members'
                ],
                'is_popular': True,
                'sort_order': 2,
            }
        )
        
        # Pro Plan - Annual
        pro_annual, created = SubscriptionPlan.objects.get_or_create(
            plan_type='pro',
            billing_period='annual',
            defaults={
                'name_ar': 'احترافي - سنوي',
                'name_en': 'Pro - Annual',
                'price': 2990,  # 20% discount
                'max_services': 20,
                'max_team_members': 5,
                'has_advanced_analytics': True,
                'has_priority_support': False,
                'search_ranking_boost': 1.2,
                'featured_credits_included': 5,
                'description_ar': 'للمحترفين والشركات الصغيرة - وفر 20%',
                'description_en': 'For professionals and small businesses - Save 20%',
                'features_ar': [
                    'حتى 20 خدمة نشطة',
                    'تحليلات متقدمة',
                    'تعزيز في نتائج البحث',
                    '5 رصيد ترويج شهرياً',
                    'حتى 5 أعضاء فريق',
                    'وفر 20% مع الدفع السنوي'
                ],
                'features_en': [
                    'Up to 20 active services',
                    'Advanced analytics',
                    'Search ranking boost',
                    '5 featured credits monthly',
                    'Up to 5 team members',
                    'Save 20% with annual billing'
                ],
                'sort_order': 3,
            }
        )
        
        # Business Plan - Monthly
        business_monthly, created = SubscriptionPlan.objects.get_or_create(
            plan_type='business',
            billing_period='monthly',
            defaults={
                'name_ar': 'أعمال - شهري',
                'name_en': 'Business - Monthly',
                'price': 799,
                'max_services': 999999,  # Unlimited
                'max_team_members': 999999,  # Unlimited
                'has_advanced_analytics': True,
                'has_priority_support': True,
                'search_ranking_boost': 1.5,
                'featured_credits_included': 20,
                'description_ar': 'للشركات الكبيرة والمؤسسات',
                'description_en': 'For large businesses and enterprises',
                'features_ar': [
                    'خدمات غير محدودة',
                    'أعضاء فريق غير محدود',
                    'تحليلات متقدمة',
                    'دعم فني متقدم',
                    'تعزيز قوي في البحث',
                    '20 رصيد ترويج شهرياً'
                ],
                'features_en': [
                    'Unlimited services',
                    'Unlimited team members',
                    'Advanced analytics',
                    'Priority support',
                    'Strong search boost',
                    '20 featured credits monthly'
                ],
                'sort_order': 4,
            }
        )
        
        # Business Plan - Annual
        business_annual, created = SubscriptionPlan.objects.get_or_create(
            plan_type='business',
            billing_period='annual',
            defaults={
                'name_ar': 'أعمال - سنوي',
                'name_en': 'Business - Annual',
                'price': 7990,  # 20% discount
                'max_services': 999999,
                'max_team_members': 999999,
                'has_advanced_analytics': True,
                'has_priority_support': True,
                'search_ranking_boost': 1.5,
                'featured_credits_included': 20,
                'description_ar': 'للشركات الكبيرة والمؤسسات - وفر 20%',
                'description_en': 'For large businesses and enterprises - Save 20%',
                'features_ar': [
                    'خدمات غير محدودة',
                    'أعضاء فريق غير محدود',
                    'تحليلات متقدمة',
                    'دعم فني متقدم',
                    'تعزيز قوي في البحث',
                    '20 رصيد ترويج شهرياً',
                    'وفر 20% مع الدفع السنوي'
                ],
                'features_en': [
                    'Unlimited services',
                    'Unlimited team members',
                    'Advanced analytics',
                    'Priority support',
                    'Strong search boost',
                    '20 featured credits monthly',
                    'Save 20% with annual billing'
                ],
                'sort_order': 5,
            }
        )

        self.stdout.write('Creating feature flags...')
        
        # Feature flags
        feature_flags = [
            {
                'key': 'advanced_analytics',
                'name_ar': 'التحليلات المتقدمة',
                'name_en': 'Advanced Analytics',
                'description_ar': 'تحليلات مفصلة للأداء والإيرادات',
                'description_en': 'Detailed performance and revenue analytics',
                'required_plan_types': ['pro', 'business'],
            },
            {
                'key': 'priority_support',
                'name_ar': 'الدعم الفني المتقدم',
                'name_en': 'Priority Support',
                'description_ar': 'دعم فني سريع ومتقدم',
                'description_en': 'Fast and advanced technical support',
                'required_plan_types': ['business'],
            },
            {
                'key': 'team_management',
                'name_ar': 'إدارة الفريق',
                'name_en': 'Team Management',
                'description_ar': 'إدارة أعضاء الفريق والصلاحيات',
                'description_en': 'Manage team members and permissions',
                'required_plan_types': ['pro', 'business'],
            },
            {
                'key': 'unlimited_services',
                'name_ar': 'خدمات غير محدودة',
                'name_en': 'Unlimited Services',
                'description_ar': 'إنشاء عدد غير محدود من الخدمات',
                'description_en': 'Create unlimited number of services',
                'required_plan_types': ['business'],
            },
        ]

        for flag_data in feature_flags:
            flag, created = FeatureFlag.objects.get_or_create(
                key=flag_data['key'],
                defaults=flag_data
            )
            
            if created:
                self.stdout.write(f'Created feature flag: {flag.name_ar}')

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded subscription plans and feature flags!')
        )