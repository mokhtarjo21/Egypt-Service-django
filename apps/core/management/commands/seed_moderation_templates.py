"""
Management command to seed moderation templates.
"""

from django.core.management.base import BaseCommand
from apps.moderation.models import ModerationTemplate


class Command(BaseCommand):
    help = 'Seed moderation templates for consistent responses'

    def handle(self, *args, **options):
        self.stdout.write('Creating moderation templates...')
        
        templates_data = [
            {
                'name': 'تحذير محتوى غير مناسب',
                'template_type': 'warning',
                'reason_codes': ['INAP_001', 'INAP_002'],
                'subject_ar': 'تحذير: محتوى غير مناسب',
                'subject_en': 'Warning: Inappropriate Content',
                'content_ar': '''مرحباً {{user_name}},

تم الإبلاغ عن محتوى غير مناسب في {{content_type}} الخاص بك. يرجى مراجعة إرشادات المجتمع والتأكد من أن جميع المحتويات تتوافق مع معاييرنا.

السبب: {{reason}}

إذا تكرر هذا السلوك، قد يتم اتخاذ إجراءات أكثر صرامة ضد حسابك.

فريق الأمان والثقة
منصة الخدمات المصرية''',
                'content_en': '''Hello {{user_name}},

Inappropriate content has been reported in your {{content_type}}. Please review our community guidelines and ensure all content complies with our standards.

Reason: {{reason}}

If this behavior continues, stricter actions may be taken against your account.

Trust & Safety Team
Egyptian Service Marketplace''',
                'variables': ['user_name', 'content_type', 'reason'],
            },
            {
                'name': 'رفض خدمة - محتوى مضلل',
                'template_type': 'rejection',
                'reason_codes': ['FAKE_002', 'PRIC_001'],
                'subject_ar': 'تم رفض خدمتك',
                'subject_en': 'Your Service Has Been Rejected',
                'content_ar': '''مرحباً {{user_name}},

للأسف، تم رفض خدمة "{{service_title}}" للأسباب التالية:

{{rejection_reason}}

يمكنك تعديل الخدمة وإعادة إرسالها للمراجعة. تأكد من:
- دقة المعلومات والأسعار
- وضوح الوصف والصور
- الالتزام بإرشادات المنصة

إذا كنت تعتقد أن هذا القرار خاطئ، يمكنك تقديم استئناف خلال 30 يوم.

فريق المراجعة
منصة الخدمات المصرية''',
                'content_en': '''Hello {{user_name}},

Unfortunately, your service "{{service_title}}" has been rejected for the following reasons:

{{rejection_reason}}

You can edit your service and resubmit for review. Please ensure:
- Accurate information and pricing
- Clear description and images
- Compliance with platform guidelines

If you believe this decision is incorrect, you can submit an appeal within 30 days.

Review Team
Egyptian Service Marketplace''',
                'variables': ['user_name', 'service_title', 'rejection_reason'],
            },
            {
                'name': 'تعليق حساب مؤقت',
                'template_type': 'suspension',
                'reason_codes': ['HARA_001', 'SPAM_001'],
                'subject_ar': 'تم تعليق حسابك مؤقتاً',
                'subject_en': 'Your Account Has Been Temporarily Suspended',
                'content_ar': '''مرحباً {{user_name}},

تم تعليق حسابك مؤقتاً حتى {{suspension_end_date}} للأسباب التالية:

{{suspension_reason}}

خلال فترة التعليق:
- لن تتمكن من تسجيل الدخول
- ستكون خدماتك مخفية مؤقتاً
- لن تتمكن من إرسال رسائل

يمكنك تقديم استئناف إذا كنت تعتقد أن هذا القرار خاطئ.

فريق الأمان والثقة
منصة الخدمات المصرية''',
                'content_en': '''Hello {{user_name}},

Your account has been temporarily suspended until {{suspension_end_date}} for the following reasons:

{{suspension_reason}}

During the suspension period:
- You will not be able to log in
- Your services will be temporarily hidden
- You will not be able to send messages

You can submit an appeal if you believe this decision is incorrect.

Trust & Safety Team
Egyptian Service Marketplace''',
                'variables': ['user_name', 'suspension_end_date', 'suspension_reason'],
            },
            {
                'name': 'قبول استئناف',
                'template_type': 'appeal_response',
                'reason_codes': [],
                'subject_ar': 'تم قبول استئنافك',
                'subject_en': 'Your Appeal Has Been Approved',
                'content_ar': '''مرحباً {{user_name}},

بعد مراجعة دقيقة لاستئنافك، قررنا قبوله وإلغاء الإجراء الإداري السابق.

تفاصيل القرار:
{{decision_notes}}

تم استعادة حسابك/محتواك بالكامل. نعتذر عن أي إزعاج قد يكون حدث.

فريق الأمان والثقة
منصة الخدمات المصرية''',
                'content_en': '''Hello {{user_name}},

After careful review of your appeal, we have decided to approve it and reverse the previous moderation action.

Decision details:
{{decision_notes}}

Your account/content has been fully restored. We apologize for any inconvenience caused.

Trust & Safety Team
Egyptian Service Marketplace''',
                'variables': ['user_name', 'decision_notes'],
            },
        ]

        for template_data in templates_data:
            template, created = ModerationTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            
            if created:
                self.stdout.write(f'Created template: {template.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded moderation templates!')
        )