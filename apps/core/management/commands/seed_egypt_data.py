"""
Management command to seed Egyptian governorates and centers data.
"""

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from apps.core.models import Province, City


class Command(BaseCommand):
    help = 'Seed Egyptian governorates and centers data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Egyptian governorates and centers...')
        
        # Egyptian governorates and their cities
        egypt_data = [
            {
                'code': 'CAI', 'name_ar': 'القاهرة', 'name_en': 'Cairo',
                'cities': [
                    {'name_ar': 'وسط البلد', 'name_en': 'Downtown'},
                    {'name_ar': 'مدينة نصر', 'name_en': 'Nasr City'},
                    {'name_ar': 'الزمالك', 'name_en': 'Zamalek'},
                    {'name_ar': 'المعادي', 'name_en': 'Maadi'},
                    {'name_ar': 'حلوان', 'name_en': 'Helwan'},
                    {'name_ar': 'شبرا الخيمة', 'name_en': 'Shubra El Kheima'},
                    {'name_ar': 'مصر الجديدة', 'name_en': 'Heliopolis'},
                    {'name_ar': 'المطرية', 'name_en': 'Matareya'},
                    {'name_ar': 'عين شمس', 'name_en': 'Ain Shams'},
                    {'name_ar': 'السلام', 'name_en': 'El Salam'},
                    {'name_ar': 'المرج', 'name_en': 'El Marg'},
                    {'name_ar': 'التجمع الخامس', 'name_en': 'Fifth Settlement'},
                    {'name_ar': 'الرحاب', 'name_en': 'Al Rehab'},
                    {'name_ar': 'مدينتي', 'name_en': 'Madinaty'},
                    {'name_ar': 'الشروق', 'name_en': 'El Shorouk'},
                    {'name_ar': 'بدر', 'name_en': 'Badr City'},
                    {'name_ar': 'العاصمة الإدارية', 'name_en': 'New Administrative Capital'},
                ]
            },
            {
                'code': 'GIZ', 'name_ar': 'الجيزة', 'name_en': 'Giza',
                'cities': [
                    {'name_ar': 'الدقي', 'name_en': 'Dokki'},
                    {'name_ar': 'المهندسين', 'name_en': 'Mohandessin'},
                    {'name_ar': 'الهرم', 'name_en': 'Haram'},
                    {'name_ar': '6 أكتوبر', 'name_en': '6th of October'},
                    {'name_ar': 'الشيخ زايد', 'name_en': 'Sheikh Zayed'},
                    {'name_ar': 'فيصل', 'name_en': 'Faisal'},
                    {'name_ar': 'إمبابة', 'name_en': 'Imbaba'},
                    {'name_ar': 'الوراق', 'name_en': 'Warraq'},
                    {'name_ar': 'العياط', 'name_en': 'Ayyat'},
                    {'name_ar': 'الصف', 'name_en': 'Saf'},
                    {'name_ar': 'أوسيم', 'name_en': 'Osim'},
                    {'name_ar': 'كرداسة', 'name_en': 'Kerdasa'},
                ]
            },
            {
                'code': 'ALX', 'name_ar': 'الإسكندرية', 'name_en': 'Alexandria',
                'cities': [
                    {'name_ar': 'المنتزه', 'name_en': 'Montaza'},
                    {'name_ar': 'وسط الإسكندرية', 'name_en': 'Alexandria Center'},
                    {'name_ar': 'الجمرك', 'name_en': 'Gomrok'},
                    {'name_ar': 'سيدي جابر', 'name_en': 'Sidi Gaber'},
                    {'name_ar': 'سموحة', 'name_en': 'Smouha'},
                    {'name_ar': 'العجمي', 'name_en': 'Agami'},
                    {'name_ar': 'العامرية', 'name_en': 'Amriya'},
                    {'name_ar': 'برج العرب', 'name_en': 'Borg El Arab'},
                    {'name_ar': 'الساحل الشمالي', 'name_en': 'North Coast'},
                ]
            },
            {
                'code': 'QAL', 'name_ar': 'القليوبية', 'name_en': 'Qalyubia',
                'cities': [
                    {'name_ar': 'بنها', 'name_en': 'Banha'},
                    {'name_ar': 'قليوب', 'name_en': 'Qalyub'},
                    {'name_ar': 'شبرا الخيمة', 'name_en': 'Shubra El Kheima'},
                    {'name_ar': 'القناطر الخيرية', 'name_en': 'Qanater El Khayreya'},
                    {'name_ar': 'الخانكة', 'name_en': 'Khanka'},
                    {'name_ar': 'كفر شكر', 'name_en': 'Kafr Shukr'},
                    {'name_ar': 'طوخ', 'name_en': 'Tukh'},
                    {'name_ar': 'العبور', 'name_en': 'Obour'},
                ]
            },
            {
                'code': 'GHR', 'name_ar': 'الغربية', 'name_en': 'Gharbia',
                'cities': [
                    {'name_ar': 'طنطا', 'name_en': 'Tanta'},
                    {'name_ar': 'المحلة الكبرى', 'name_en': 'El Mahalla El Kubra'},
                    {'name_ar': 'كفر الزيات', 'name_en': 'Kafr El Zayat'},
                    {'name_ar': 'زفتى', 'name_en': 'Zifta'},
                    {'name_ar': 'السنطة', 'name_en': 'El Santa'},
                    {'name_ar': 'قطور', 'name_en': 'Qutour'},
                    {'name_ar': 'بسيون', 'name_en': 'Basyoun'},
                    {'name_ar': 'سمنود', 'name_en': 'Samannoud'},
                ]
            },
            {
                'code': 'MNF', 'name_ar': 'المنوفية', 'name_en': 'Monufia',
                'cities': [
                    {'name_ar': 'شبين الكوم', 'name_en': 'Shibin El Kom'},
                    {'name_ar': 'منوف', 'name_en': 'Menouf'},
                    {'name_ar': 'أشمون', 'name_en': 'Ashmoun'},
                    {'name_ar': 'سرس الليان', 'name_en': 'Sers El Lyan'},
                    {'name_ar': 'تلا', 'name_en': 'Tala'},
                    {'name_ar': 'الباجور', 'name_en': 'El Bagour'},
                    {'name_ar': 'الشهداء', 'name_en': 'El Shohada'},
                    {'name_ar': 'قويسنا', 'name_en': 'Quesna'},
                    {'name_ar': 'بركة السبع', 'name_en': 'Sadat City'},
                ]
            },
            {
                'code': 'BHR', 'name_ar': 'البحيرة', 'name_en': 'Beheira',
                'cities': [
                    {'name_ar': 'دمنهور', 'name_en': 'Damanhour'},
                    {'name_ar': 'كفر الدوار', 'name_en': 'Kafr El Dawar'},
                    {'name_ar': 'رشيد', 'name_en': 'Rashid'},
                    {'name_ar': 'إدكو', 'name_en': 'Edco'},
                    {'name_ar': 'أبو المطامير', 'name_en': 'Abu al-Matamir'},
                    {'name_ar': 'أبو حمص', 'name_en': 'Abu Homs'},
                    {'name_ar': 'الدلنجات', 'name_en': 'Delengat'},
                    {'name_ar': 'المحمودية', 'name_en': 'Mahmoudiyah'},
                    {'name_ar': 'الرحمانية', 'name_en': 'Rahmaniya'},
                    {'name_ar': 'إيتاي البارود', 'name_en': 'Itay El Barud'},
                    {'name_ar': 'حوش عيسى', 'name_en': 'Hosh Issa'},
                    {'name_ar': 'شبراخيت', 'name_en': 'Shubrakhit'},
                    {'name_ar': 'كوم حمادة', 'name_en': 'Kom Hamada'},
                    {'name_ar': 'بدر', 'name_en': 'Badr'},
                    {'name_ar': 'وادي النطرون', 'name_en': 'Wadi El Natrun'},
                    {'name_ar': 'النوبارية الجديدة', 'name_en': 'New Nubaria'},
                ]
            },
            {
                'code': 'DKH', 'name_ar': 'الدقهلية', 'name_en': 'Dakahlia',
                'cities': [
                    {'name_ar': 'المنصورة', 'name_en': 'Mansoura'},
                    {'name_ar': 'طلخا', 'name_en': 'Talkha'},
                    {'name_ar': 'ميت غمر', 'name_en': 'Mit Ghamr'},
                    {'name_ar': 'دكرنس', 'name_en': 'Dekernes'},
                    {'name_ar': 'أجا', 'name_en': 'Aga'},
                    {'name_ar': 'منية النصر', 'name_en': 'Menia El Nasr'},
                    {'name_ar': 'السنبلاوين', 'name_en': 'Sinbillawin'},
                    {'name_ar': 'الكردي', 'name_en': 'El Kurdi'},
                    {'name_ar': 'بني عبيد', 'name_en': 'Bani Ubaid'},
                    {'name_ar': 'المنزلة', 'name_en': 'Al Manzala'},
                    {'name_ar': 'تمى الأمديد', 'name_en': 'Tami El Amdid'},
                    {'name_ar': 'الجمالية', 'name_en': 'El Gamaliya'},
                    {'name_ar': 'شربين', 'name_en': 'Sherbin'},
                    {'name_ar': 'المطرية', 'name_en': 'Matareya'},
                    {'name_ar': 'بلقاس', 'name_en': 'Belqas'},
                    {'name_ar': 'ميت سلسيل', 'name_en': 'Mit Salsil'},
                    {'name_ar': 'جمصة', 'name_en': 'Gamasa'},
                    {'name_ar': 'محلة دمنة', 'name_en': 'Mahalat Damana'},
                    {'name_ar': 'نبروه', 'name_en': 'Nabroh'},
                ]
            },
            {
                'code': 'KFS', 'name_ar': 'كفر الشيخ', 'name_en': 'Kafr el-Sheikh',
                'cities': [
                    {'name_ar': 'كفر الشيخ', 'name_en': 'Kafr El Sheikh'},
                    {'name_ar': 'دسوق', 'name_en': 'Desouk'},
                    {'name_ar': 'فوّه', 'name_en': 'Fooh'},
                    {'name_ar': 'مطوبس', 'name_en': 'Metoubes'},
                    {'name_ar': 'برج البرلس', 'name_en': 'Baltim'},
                    {'name_ar': 'بلطيم', 'name_en': 'Baltim Resort'},
                    {'name_ar': 'مسير', 'name_en': 'Masir'},
                    {'name_ar': 'الرياض', 'name_en': 'El Riad'},
                    {'name_ar': 'سيدي سالم', 'name_en': 'Sidi Salem'},
                    {'name_ar': 'قلين', 'name_en': 'Qalin'},
                    {'name_ar': 'سيدي غازي', 'name_en': 'Sidi Ghazi'},
                    {'name_ar': 'بيلا', 'name_en': 'Biyala'},
                    {'name_ar': 'الحامول', 'name_en': 'El Hamool'},
                ]
            },
            {
                'code': 'DMT', 'name_ar': 'دمياط', 'name_en': 'Damietta',
                'cities': [
                    {'name_ar': 'دمياط', 'name_en': 'Damietta'},
                    {'name_ar': 'دمياط الجديدة', 'name_en': 'New Damietta'},
                    {'name_ar': 'رأس البر', 'name_en': 'Ras El Bar'},
                    {'name_ar': 'فارسكور', 'name_en': 'Faraskour'},
                    {'name_ar': 'الزرقا', 'name_en': 'Zarqa'},
                    {'name_ar': 'السرو', 'name_en': 'Alsaro'},
                    {'name_ar': 'الروضة', 'name_en': 'Al Rawda'},
                    {'name_ar': 'كفر البطيخ', 'name_en': 'Kafr El Batikh'},
                    {'name_ar': 'عزبة البرج', 'name_en': 'Ezbet El Borg'},
                    {'name_ar': 'ميت أبو غالب', 'name_en': 'Mit Abu Ghaleb'},
                    {'name_ar': 'كفر سعد', 'name_en': 'Kafr Saad'},
                ]
            },
            {
                'code': 'SHR', 'name_ar': 'الشرقية', 'name_en': 'Sharqia',
                'cities': [
                    {'name_ar': 'الزقازيق', 'name_en': 'Zagazig'},
                    {'name_ar': 'العشر من رمضان', 'name_en': '10th of Ramadan'},
                    {'name_ar': 'منيا القمح', 'name_en': 'Minya El Qamh'},
                    {'name_ar': 'بلبيس', 'name_en': 'Belbeis'},
                    {'name_ar': 'مشتول السوق', 'name_en': 'Mashtoul El Souq'},
                    {'name_ar': 'القنايات', 'name_en': 'Qenayat'},
                    {'name_ar': 'أبو حماد', 'name_en': 'Abu Hammad'},
                    {'name_ar': 'القرين', 'name_en': 'El Qurain'},
                    {'name_ar': 'ههيا', 'name_en': 'Hehia'},
                    {'name_ar': 'أبو كبير', 'name_en': 'Abu Kabir'},
                    {'name_ar': 'فاقوس', 'name_en': 'Facus'},
                    {'name_ar': 'الصالحية الجديدة', 'name_en': 'El Salheya El Gedida'},
                    {'name_ar': 'الإبراهيمية', 'name_en': 'Al Ibrahimiyah'},
                    {'name_ar': 'ديرب نجم', 'name_en': 'Deirb Negm'},
                    {'name_ar': 'كفر صقر', 'name_en': 'Kafr Saqr'},
                    {'name_ar': 'أولاد صقر', 'name_en': 'Awlad Saqr'},
                    {'name_ar': 'الحسينية', 'name_en': 'Husseiniya'},
                    {'name_ar': 'صان الحجر القبلية', 'name_en': 'San El Hagar'},
                    {'name_ar': 'منشأة أبو عمر', 'name_en': 'Manshayat Abu Omar'},
                ]
            },
            {
                'code': 'POR', 'name_ar': 'بورسعيد', 'name_en': 'Port Said',
                'cities': [
                    {'name_ar': 'حي الشرق', 'name_en': 'Sharq District'},
                    {'name_ar': 'حي العرب', 'name_en': 'Arab District'},
                    {'name_ar': 'حي المناخ', 'name_en': 'Manakh District'},
                    {'name_ar': 'حي الضواحي', 'name_en': 'Dawahi District'},
                    {'name_ar': 'حي الجنوب', 'name_en': 'South District'},
                    {'name_ar': 'حي الزهور', 'name_en': 'Zohour District'},
                    {'name_ar': 'حي غرب', 'name_en': 'West District'},
                    {'name_ar': 'بورفؤاد', 'name_en': 'Port Fuad'},
                ]
            },
            {
                'code': 'ISM', 'name_ar': 'الإسماعيلية', 'name_en': 'Ismailia',
                'cities': [
                    {'name_ar': 'الإسماعيلية', 'name_en': 'Ismailia'},
                    {'name_ar': 'فايد', 'name_en': 'Fayed'},
                    {'name_ar': 'القنطرة شرق', 'name_en': 'Qantara Sharq'},
                    {'name_ar': 'القنطرة غرب', 'name_en': 'Qantara Gharb'},
                    {'name_ar': 'التل الكبير', 'name_en': 'El Tal El Kabir'},
                    {'name_ar': 'أبو صوير', 'name_en': 'Abu Sawir'},
                    {'name_ar': 'القصاصين الجديدة', 'name_en': 'Kasasine El Gedida'},
                ]
            },
            {
                'code': 'SUZ', 'name_ar': 'السويس', 'name_en': 'Suez',
                'cities': [
                    {'name_ar': 'السويس', 'name_en': 'Suez'},
                    {'name_ar': 'حي الأربعين', 'name_en': 'Arbaeen District'},
                    {'name_ar': 'حي عتاقة', 'name_en': 'Attaka District'},
                    {'name_ar': 'حي فيصل', 'name_en': 'Faisal District'},
                    {'name_ar': 'حي الجناين', 'name_en': 'Ganayen District'},
                ]
            },
             {
                'code': 'MAT', 'name_ar': 'مطروح', 'name_en': 'Matrouh',
                'cities': [
                    {'name_ar': 'مرسى مطروح', 'name_en': 'Marsa Matrouh'},
                    {'name_ar': 'الحمام', 'name_en': 'El Hamam'},
                    {'name_ar': 'العلمين', 'name_en': 'Alamein'},
                    {'name_ar': 'الضبعة', 'name_en': 'Dabaa'},
                    {'name_ar': 'النجيلة', 'name_en': 'Al-Nagila'},
                    {'name_ar': 'سيدي براني', 'name_en': 'Sidi Barrani'},
                    {'name_ar': 'السلوم', 'name_en': 'Salloum'},
                    {'name_ar': 'سيوة', 'name_en': 'Siwa'},
                ]
            },
            {
                'code': 'NOR', 'name_ar': 'شمال سيناء', 'name_en': 'North Sinai',
                'cities': [
                    {'name_ar': 'العريش', 'name_en': 'Arish'},
                    {'name_ar': 'الشيخ زويد', 'name_en': 'Sheikh Zuweid'},
                    {'name_ar': 'رفح', 'name_en': 'Rafah'},
                    {'name_ar': 'بئر العبد', 'name_en': 'Bir El Abd'},
                    {'name_ar': 'الحسنة', 'name_en': 'Hasna'},
                    {'name_ar': 'نخل', 'name_en': 'Nakhl'},
                ]
            },
            {
                'code': 'SOU', 'name_ar': 'جنوب سيناء', 'name_en': 'South Sinai',
                'cities': [
                    {'name_ar': 'الطور', 'name_en': 'El Tor'},
                    {'name_ar': 'شرم الشيخ', 'name_en': 'Sharm El Sheikh'},
                    {'name_ar': 'دهب', 'name_en': 'Dahab'},
                    {'name_ar': 'نويبع', 'name_en': 'Nuweiba'},
                    {'name_ar': 'طابا', 'name_en': 'Taba'},
                    {'name_ar': 'سانت كاترين', 'name_en': 'Saint Catherine'},
                    {'name_ar': 'أبو رديس', 'name_en': 'Abu Redis'},
                    {'name_ar': 'أبو زنيمة', 'name_en': 'Abu Zenima'},
                    {'name_ar': 'رأس سدر', 'name_en': 'Ras Sudr'},
                ]
            },
           {
                'code': 'FYM', 'name_ar': 'الفيوم', 'name_en': 'Faiyum',
                'cities': [
                    {'name_ar': 'الفيوم', 'name_en': 'Faiyum'},
                    {'name_ar': 'الفيوم الجديدة', 'name_en': 'New Faiyum'},
                    {'name_ar': 'طامية', 'name_en': 'Tamiya'},
                    {'name_ar': 'سنورس', 'name_en': 'Snores'},
                    {'name_ar': 'إطسا', 'name_en': 'Etsa'},
                    {'name_ar': 'إبشواي', 'name_en': 'Ibshway'},
                    {'name_ar': 'يوسف الصديق', 'name_en': 'Yusuf El Sediaq'},
                ]
            },
            {
                'code': 'BNS', 'name_ar': 'بني سويف', 'name_en': 'Beni Suef',
                'cities': [
                    {'name_ar': 'بني سويف', 'name_en': 'Beni Suef'},
                    {'name_ar': 'بني سويف الجديدة', 'name_en': 'New Beni Suef'},
                    {'name_ar': 'الواسطى', 'name_en': 'Al Wasta'},
                    {'name_ar': 'ناصر', 'name_en': 'Nasser'},
                    {'name_ar': 'إهناسيا', 'name_en': 'Ihnasiya'},
                    {'name_ar': 'ببا', 'name_en': 'Biba'},
                    {'name_ar': 'الفشن', 'name_en': 'Fashn'},
                    {'name_ar': 'سمسطا', 'name_en': 'Samasta'},
                ]
            },
            {
                'code': 'MIN', 'name_ar': 'المنيا', 'name_en': 'Minya',
                'cities': [
                    {'name_ar': 'المنيا', 'name_en': 'Minya'},
                    {'name_ar': 'المنيا الجديدة', 'name_en': 'New Minya'},
                    {'name_ar': 'العدوة', 'name_en': 'El Idwa'},
                    {'name_ar': 'مغاغة', 'name_en': 'Maghagha'},
                    {'name_ar': 'بني مزار', 'name_en': 'Bani Mazar'},
                    {'name_ar': 'مطاي', 'name_en': 'Mattay'},
                    {'name_ar': 'سمالوط', 'name_en': 'Samalut'},
                    {'name_ar': 'أبو قرقاص', 'name_en': 'Abu Qurqas'},
                    {'name_ar': 'ملوي', 'name_en': 'Meloy'},
                    {'name_ar': 'دير مواس', 'name_en': 'Deir Mawas'},
                ]
            },
            {
                'code': 'ASY', 'name_ar': 'أسيوط', 'name_en': 'Asyut',
                'cities': [
                    {'name_ar': 'أسيوط', 'name_en': 'Asyut'},
                    {'name_ar': 'أسيوط الجديدة', 'name_en': 'New Asyut'},
                    {'name_ar': 'ديروط', 'name_en': 'Dayrout'},
                    {'name_ar': 'منفلوط', 'name_en': 'Manfalut'},
                    {'name_ar': 'القوصية', 'name_en': 'Qusiya'},
                    {'name_ar': 'أبنوب', 'name_en': 'Abnoub'},
                    {'name_ar': 'أبو تيج', 'name_en': 'Abu Tig'},
                    {'name_ar': 'الغنايم', 'name_en': 'El Ghanaim'},
                    {'name_ar': 'ساحل سليم', 'name_en': 'Sahel Selim'},
                    {'name_ar': 'البداري', 'name_en': 'El Badari'},
                    {'name_ar': 'صدفا', 'name_en': 'Sidfa'},
                ]
            },
            {
                'code': 'SOH', 'name_ar': 'سوهاج', 'name_en': 'Sohag',
                'cities': [
                    {'name_ar': 'سوهاج', 'name_en': 'Sohag'},
                    {'name_ar': 'سوهاج الجديدة', 'name_en': 'New Sohag'},
                    {'name_ar': 'أخميم', 'name_en': 'Akhmim'},
                    {'name_ar': 'أخميم الجديدة', 'name_en': 'New Akhmim'},
                    {'name_ar': 'البلينا', 'name_en': 'Al Balyana'},
                    {'name_ar': 'المراغة', 'name_en': 'El Maragha'},
                    {'name_ar': 'المنشأة', 'name_en': 'al-Munsha\'a'},
                    {'name_ar': 'دار السلام', 'name_en': 'Dar El Salam'},
                    {'name_ar': 'جرجا', 'name_en': 'Gerga'},
                    {'name_ar': 'جهينة', 'name_en': 'Juhayna'},
                    {'name_ar': 'ساقلتة', 'name_en': 'Saqulta'},
                    {'name_ar': 'طما', 'name_en': 'Tama'},
                    {'name_ar': 'طهطا', 'name_en': 'Tahta'},
                ]
            },
            {
                'code': 'QNA', 'name_ar': 'قنا', 'name_en': 'Qena',
                'cities': [
                    {'name_ar': 'قنا', 'name_en': 'Qena'},
                    {'name_ar': 'قنا الجديدة', 'name_en': 'New Qena'},
                    {'name_ar': 'أبو تشت', 'name_en': 'Abu Tesht'},
                    {'name_ar': 'نجع حمادي', 'name_en': 'Nag Hammadi'},
                    {'name_ar': 'دشنا', 'name_en': 'Deshna'},
                    {'name_ar': 'الوقف', 'name_en': 'Alwaqf'},
                    {'name_ar': 'قفط', 'name_en': 'Qift'},
                    {'name_ar': 'نقادة', 'name_en': 'Naqada'},
                    {'name_ar': 'قوص', 'name_en': 'Qus'},
                    {'name_ar': 'فرشوط', 'name_en': 'Farshut'},
                ]
            },
            {
                'code': 'LUX', 'name_ar': 'الأقصر', 'name_en': 'Luxor',
                'cities': [
                    {'name_ar': 'الأقصر', 'name_en': 'Luxor'},
                    {'name_ar': 'الأقصر الجديدة', 'name_en': 'New Luxor'},
                    {'name_ar': 'إسنا', 'name_en': 'Esna'},
                    {'name_ar': 'طيب الجديدة', 'name_en': 'New Tiba'},
                    {'name_ar': 'الزينية', 'name_en': 'Al Zinia'},
                    {'name_ar': 'البياضية', 'name_en': 'Al Bayadiya'},
                    {'name_ar': 'القرنة', 'name_en': 'Al Qarna'},
                    {'name_ar': 'أرمنت', 'name_en': 'Armant'},
                    {'name_ar': 'الطود', 'name_en': 'Al Tud'},
                ]
            },
            {
                'code': 'ASW', 'name_ar': 'أسوان', 'name_en': 'Aswan',
                'cities': [
                    {'name_ar': 'أسوان', 'name_en': 'Aswan'},
                    {'name_ar': 'أسوان الجديدة', 'name_en': 'New Aswan'},
                    {'name_ar': 'دراو', 'name_en': 'Daraw'},
                    {'name_ar': 'كوم أمبو', 'name_en': 'Kom Ombo'},
                    {'name_ar': 'نصر النوبة', 'name_en': 'Nasr Al Nuba'},
                    {'name_ar': 'إدفو', 'name_en': 'Edfu'},
                ]
            },
            {
                'code': 'RED', 'name_ar': 'البحر الأحمر', 'name_en': 'Red Sea',
                'cities': [
                    {'name_ar': 'الغردقة', 'name_en': 'Hurghada'},
                    {'name_ar': 'رأس غارب', 'name_en': 'Ras Ghareb'},
                    {'name_ar': 'سفاجا', 'name_en': 'Safaga'},
                    {'name_ar': 'القصير', 'name_en': 'El Qusiar'},
                    {'name_ar': 'مرسى علم', 'name_en': 'Marsa Alam'},
                    {'name_ar': 'الشلاتين', 'name_en': 'Shalatin'},
                    {'name_ar': 'حلايب', 'name_en': 'Halaib'},
                ]
            },
            {
                'code': 'WAD', 'name_ar': 'الوادي الجديد', 'name_en': 'New Valley',
                'cities': [
                    {'name_ar': 'الخارجة', 'name_en': 'Kharga'},
                    {'name_ar': 'باريس', 'name_en': 'Paris'},
                    {'name_ar': 'موط', 'name_en': 'Mut'},
                    {'name_ar': 'الفرافرة', 'name_en': 'Farafra'},
                    {'name_ar': 'بلاط', 'name_en': 'Balat'},
                ]
            },
        ]
        
        created_provinces = 0
        created_cities = 0

        for gov_data in egypt_data:
            province, created = Province.objects.get_or_create(
                code=gov_data['code'],
                defaults={
                    'name_ar': gov_data['name_ar'],
                    'name_en': gov_data['name_en']
                }
            )
            if created:
                created_provinces += 1
                self.stdout.write(f'Created governorate: {province.name_ar}')
            
            cities_data = gov_data.get('cities', [])
            for city_data in cities_data:
                city, city_created = City.objects.get_or_create(
                    province=province,
                    name_ar=city_data['name_ar'],
                    defaults={'name_en': city_data['name_en']}
                )
                if city_created:
                    created_cities += 1
                    
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_provinces} governorates and {created_cities} cities!'
            )
        )