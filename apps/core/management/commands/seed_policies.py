"""
Management command to seed policy documents.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.moderation.models import PolicyVersion

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed policy documents'

    def handle(self, *args, **options):
        self.stdout.write('Creating policy documents...')
        
        # Get or create admin user for policy creation
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            self.stdout.write(
                self.style.WARNING('No admin user found. Please create an admin user first.')
            )
            return

        policies_data = [
            {
                'policy_type': 'terms',
                'version': '1.0',
                'title_ar': 'شروط الخدمة',
                'title_en': 'Terms of Service',
                'content_ar': '''# شروط الخدمة - منصة الخدمات المصرية

## 1. القبول بالشروط
باستخدام منصة الخدمات المصرية، فإنك توافق على الالتزام بهذه الشروط والأحكام.

## 2. الأهلية
- يجب أن تكون 18 سنة أو أكثر
- يجب أن تكون مقيماً في مصر
- يجب تقديم معلومات صحيحة ودقيقة

## 3. الحسابات
- مسؤول عن الحفاظ على سرية حسابك
- إشعارنا فوراً بأي استخدام غير مصرح به
- حساب واحد لكل شخص

## 4. الخدمات
- يجب أن تكون الخدمات قانونية ومشروعة
- وصف دقيق للخدمات والأسعار
- الالتزام بجودة الخدمة المعلن عنها

## 5. المدفوعات
- جميع المدفوعات بالجنيه المصري
- رسوم المنصة كما هو محدد
- سياسة الاسترداد حسب الحالة

## 6. المسؤولية
- المنصة وسيط بين مقدمي الخدمات والعملاء
- لا نتحمل مسؤولية جودة الخدمات
- التأمين والضمانات مسؤولية مقدم الخدمة

## 7. الإنهاء
- يحق لنا إنهاء الحسابات المخالفة
- يمكنك إلغاء حسابك في أي وقت
- البيانات المحفوظة حسب سياسة الخصوصية

تاريخ النفاذ: 1 يناير 2024''',
                'content_en': '''# Terms of Service - Egyptian Service Marketplace

## 1. Acceptance of Terms
By using the Egyptian Service Marketplace, you agree to be bound by these terms and conditions.

## 2. Eligibility
- Must be 18 years or older
- Must be a resident of Egypt
- Must provide accurate and truthful information

## 3. Accounts
- Responsible for maintaining account confidentiality
- Notify us immediately of unauthorized use
- One account per person

## 4. Services
- Services must be legal and legitimate
- Accurate description of services and pricing
- Commitment to advertised service quality

## 5. Payments
- All payments in Egyptian Pounds
- Platform fees as specified
- Refund policy as applicable

## 6. Liability
- Platform is intermediary between providers and customers
- We do not guarantee service quality
- Insurance and warranties are provider responsibility

## 7. Termination
- We may terminate accounts for violations
- You may cancel your account anytime
- Data retention per privacy policy

Effective Date: January 1, 2024''',
                'change_summary': 'Initial version of terms of service',
                'is_active': True,
                'effective_date': timezone.now(),
                'created_by': admin_user,
            },
            {
                'policy_type': 'privacy',
                'version': '1.0',
                'title_ar': 'سياسة الخصوصية',
                'title_en': 'Privacy Policy',
                'content_ar': '''# سياسة الخصوصية - منصة الخدمات المصرية

## 1. المعلومات التي نجمعها
- معلومات الحساب: الاسم، رقم الهاتف، البريد الإلكتروني
- معلومات الموقع: المحافظة والمركز
- مستندات التحقق: صورة البطاقة الشخصية
- بيانات الاستخدام: تفاعلك مع المنصة

## 2. كيف نستخدم المعلومات
- تقديم وتحسين خدماتنا
- التحقق من الهوية والأمان
- التواصل معك حول حسابك
- الامتثال للمتطلبات القانونية

## 3. مشاركة المعلومات
- لا نبيع معلوماتك الشخصية
- نشارك المعلومات فقط عند الضرورة القانونية
- مقدمو الخدمات يرون معلومات التواصل الأساسية

## 4. أمان البيانات
- تشفير البيانات الحساسة
- تخزين آمن لمستندات الهوية
- مراجعة أمنية دورية

## 5. حقوقك
- الوصول إلى بياناتك
- تصحيح المعلومات الخاطئة
- حذف الحساب والبيانات
- نقل البيانات

## 6. الاحتفاظ بالبيانات
- نحتفظ بالبيانات طالما كان الحساب نشطاً
- حذف البيانات خلال 90 يوم من إلغاء الحساب
- الاحتفاظ بسجلات الأمان لمدة سنة

## 7. ملفات تعريف الارتباط
- نستخدم ملفات تعريف الارتباط لتحسين التجربة
- يمكنك التحكم في إعدادات ملفات تعريف الارتباط

## 8. التحديثات
- سنخطرك بأي تغييرات مهمة
- المراجعة الدورية لهذه السياسة

للاستفسارات: privacy@marketplace.eg

تاريخ النفاذ: 1 يناير 2024''',
                'content_en': '''# Privacy Policy - Egyptian Service Marketplace

## 1. Information We Collect
- Account information: name, phone, email
- Location information: governorate and center
- Verification documents: national ID photos
- Usage data: your interaction with the platform

## 2. How We Use Information
- Provide and improve our services
- Verify identity and security
- Communicate about your account
- Comply with legal requirements

## 3. Information Sharing
- We do not sell your personal information
- Share information only when legally required
- Service providers see basic contact information

## 4. Data Security
- Encryption of sensitive data
- Secure storage of identity documents
- Regular security reviews

## 5. Your Rights
- Access your data
- Correct inaccurate information
- Delete account and data
- Data portability

## 6. Data Retention
- Retain data while account is active
- Delete data within 90 days of account closure
- Retain security logs for one year

## 7. Cookies
- Use cookies to improve experience
- You can control cookie settings

## 8. Updates
- We will notify you of important changes
- Regular review of this policy

For inquiries: privacy@marketplace.eg

Effective Date: January 1, 2024''',
                'change_summary': 'Initial privacy policy',
                'is_active': True,
                'effective_date': timezone.now(),
                'created_by': admin_user,
            },
            {
                'policy_type': 'community',
                'version': '1.0',
                'title_ar': 'إرشادات المجتمع',
                'title_en': 'Community Guidelines',
                'content_ar': '''# إرشادات المجتمع - منصة الخدمات المصرية

## مرحباً بك في مجتمعنا
نسعى لخلق بيئة آمنة وموثوقة لجميع المستخدمين. هذه الإرشادات تساعد في الحفاظ على جودة المنصة.

## ما نشجعه
- **الصدق والشفافية**: وصف دقيق للخدمات والأسعار
- **الاحترام المتبادل**: تعامل مهذب مع جميع المستخدمين
- **الجودة العالية**: تقديم خدمات تلبي أو تتجاوز التوقعات
- **التواصل الفعال**: الرد السريع على الاستفسارات

## ما لا نسمح به
- **المحتوى المضلل**: معلومات خاطئة أو مضللة
- **التحرش**: أي شكل من أشكال التحرش أو الإزعاج
- **المحتوى غير المناسب**: محتوى جنسي أو عنيف أو مسيء
- **الاحتيال**: محاولات النصب أو الاحتيال
- **انتهاك الخصوصية**: مشاركة معلومات شخصية بدون إذن

## الخدمات المحظورة
- الخدمات غير القانونية
- بيع المواد المحظورة
- الخدمات التي تنتهك حقوق الآخرين
- الأنشطة التي تضر بالأمان العام

## العواقب
- **التحذير**: للمخالفات البسيطة
- **إخفاء المحتوى**: للمحتوى المخالف
- **تعليق الحساب**: للمخالفات المتكررة
- **الحظر الدائم**: للمخالفات الجسيمة

## الإبلاغ
إذا واجهت محتوى مخالف، يرجى الإبلاغ عنه فوراً. نراجع جميع البلاغات خلال 24-48 ساعة.

## الاستئناف
يمكنك استئناف أي إجراء إداري خلال 30 يوم من تاريخ الإجراء.

شكراً لمساعدتك في الحفاظ على مجتمع آمن وموثوق.

فريق الأمان والثقة
منصة الخدمات المصرية''',
                'content_en': '''# Community Guidelines - Egyptian Service Marketplace

## Welcome to Our Community
We strive to create a safe and trustworthy environment for all users. These guidelines help maintain platform quality.

## What We Encourage
- **Honesty and Transparency**: Accurate service descriptions and pricing
- **Mutual Respect**: Courteous interaction with all users
- **High Quality**: Services that meet or exceed expectations
- **Effective Communication**: Quick response to inquiries

## What We Don't Allow
- **Misleading Content**: False or misleading information
- **Harassment**: Any form of harassment or abuse
- **Inappropriate Content**: Sexual, violent, or offensive content
- **Fraud**: Attempts at scamming or fraud
- **Privacy Violations**: Sharing personal information without consent

## Prohibited Services
- Illegal services
- Sale of prohibited materials
- Services that violate others' rights
- Activities that harm public safety

## Consequences
- **Warning**: For minor violations
- **Content Hidden**: For violating content
- **Account Suspension**: For repeated violations
- **Permanent Ban**: For serious violations

## Reporting
If you encounter violating content, please report it immediately. We review all reports within 24-48 hours.

## Appeals
You can appeal any moderation action within 30 days of the action date.

Thank you for helping maintain a safe and trustworthy community.

Trust & Safety Team
Egyptian Service Marketplace''',
                'change_summary': 'Initial community guidelines',
                'is_active': True,
                'effective_date': timezone.now(),
                'created_by': admin_user,
            },
        ]

        for policy_data in policies_data:
            policy, created = PolicyVersion.objects.get_or_create(
                policy_type=policy_data['policy_type'],
                version=policy_data['version'],
                defaults=policy_data
            )
            
            if created:
                self.stdout.write(f'Created policy: {policy.title_ar}')

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded policy documents!')
        )