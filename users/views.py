
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
from django.conf import settings
from django.utils.timezone import now 
from django.contrib.auth.models import AnonymousUser
from django.views import View
from .models import *
import random
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from rest_framework.pagination import PageNumberPagination
import string
from django.http import QueryDict
from rest_framework.parsers import MultiPartParser, FormParser
from datetime import datetime, timedelta
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from .serializers import *
from django.http import JsonResponse
import json

from django.core.cache import cache
from rest_framework.decorators import api_view , permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.contrib.auth.hashers import check_password, make_password
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics, filters


class AdminUserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class AllUsersListView(generics.ListAPIView):
    print("AllUsersListView")
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]  # <-- change to AllowAny if public
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['fullName', 'phoneNumber']
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({'username': self.user.username})
        user_data = CurrentUserSerializer(self.user).data
        data['user'] = user_data

        
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    print("CustomTokenObtainPairView")
    serializer_class = CustomTokenObtainPairSerializer
    

class check_email(APIView):
    def post(self,request):
        email = request.data.get('email')
        exists = User.objects.filter(email=email).exists()
        print("Email:", email)
        if exists:
            user = User.objects.get(email=email)
            active = user.active_email
            print("Email:", email)
        
            if active:
                return Response({'user': '1'}, status=status.HTTP_200_OK)

        return Response({'user': '0'}, status=status.HTTP_200_OK)
  

       
class RegisterView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        print("Request Data:", request.data)  # Debug
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            phoneNumber=request.data.get('phoneNumber')
            user = User.objects.get(phoneNumber=phoneNumber)
            activation_code = ''.join(random.choices(string.digits, k=6))
            User_active.objects.create(user=user, active=activation_code)
            cache.delete('users_list')  # Clear cache after user registration
            return Response({"message": "تم التسجيل بنجاح"}, status=201)
        return Response(serializer.errors, status=400)
       
        

 
def send(email):
    user = User.objects.get(phoneNumber=email)
    use_active = None
    exitsst = User_active.objects.filter(user=user).exists()
    if exitsst:
        use_active = User_active.objects.get(user=user)
    else:
        activation_code = ''.join(random.choices(string.digits, k=6))
        User_active.objects.create(user=user, active=activation_code)
    if now() - use_active.time_send > timedelta(days=1):
        activation_code = ''.join(random.choices(string.digits, k=6))
        use_active.active = activation_code
        use_active.time_send = now()
        use_active.save()

    otp = use_active.active
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)



    # verification = client.verify \
    # .v2 \
    # .services('VA601d826cb913def895fd3edce8d9a59b') \
    # .verifications \
    # .create(to=f'+2{email}', channel='sms',body=f'رمز التحقق الخاص بك هو: {otp}',)
    message = client.messages.create(
    body=f'رمز التحقق الخاص بك هو: {otp}',    
    from_='whatsapp:+14155238886',
    # content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
    # content_variables=f'{"1":"رمز التحقق الخاص بك هو","2":"{otp}"}',
    to=f'whatsapp:+2{email}'
)
    # message = client.messages.create(
    #     body=f'رمز التحقق الخاص بك هو: {otp}',
    #     from_=settings.TWILIO_PHONE_NUMBER,
    #     to=f'+2{email}'  
    # )
    return message.sid
    # return verification.sid
@api_view(['post'])
def send_activation_email(request):
    print("Request Data:", request.data)
    phoneNumber = request.data.get('phoneNumber')
    send(phoneNumber)
    
    
    return Response({'message': 'من فضلك تفقد واتساب الخاص بك لاستلام رمز التاكيد'}, status=status.HTTP_200_OK)

    
class ActivationView(APIView):
    def post(self, request):
        phoneNumber = request.data.get('phoneNumber')
        code = request.data.get('otp')
        print("code:", code)
        user = User.objects.get(phoneNumber=phoneNumber)

        use_active = User_active.objects.get(user=user)
        if use_active.active == code and now() - use_active.time_send < timedelta(days=1):
            user.isPhoneVerified = True
            user.save()
            return Response({'message': 'تم تفعيل الرقم الخاص بك بنجاح'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'تم انتهاء صلاحية الرمز.'}, status=status.HTTP_400_BAD_REQUEST)

class all_users(APIView):
    

    def get(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        users = User.objects.all()
        serializer = CurrentUserSerializer(users, many=True)
        users_data = serializer.data
        cache.set('users_list', users_data, timeout=60 * 5)
        
        return Response(users_data, status=status.HTTP_200_OK)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class verify(APIView):
    def patch(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        phoneNumber = request.data.get('phoneNumber')
        verificationStatus = request.data.get('verificationStatus', '').lower()
        
        print("Phone Number:", phoneNumber)
        print("Verification Status:", verificationStatus)

        if verificationStatus not in ['approved', 'rejected']:
            return Response({'error': 'Invalid verification status.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phoneNumber=phoneNumber)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        user.verificationStatus = verificationStatus
        user.isVerified = (verificationStatus == 'approved')
        user.isActive = (verificationStatus == 'approved')
        user.save()

        users = User.objects.all()
        serializer = CurrentUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class userSaveInfo(APIView):
    

    def post(self, request):
        user = request.user
        print("User:", user)
        password = request.data.get('currentPassword')
        new_password = request.data.get('newPassword')
        if not user.check_password(password):
            return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_401_UNAUTHORIZED)
        if new_password:
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)
        return Response({'error': 'New password is required.'}, status=status.HTTP_400_BAD_REQUEST)

        

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user

    if isinstance(request.data, QueryDict):
        data = request.data.copy()
        governorates_list = request.data.getlist('governorates[]')
        centers_list = request.data.getlist('centers[]')
    else:
        data = request.data
        governorates_list = data.get('governorates[]', [])
        centers_list = data.get('centers[]', [])



    serializer = UserRegisterSerializer(user, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()

        # مسح القديم
        governorates.objects.filter(user=user).delete()
        cities.objects.filter(user=user).delete()

        # إضافة الجديد
        for gov in governorates_list:
            if gov:
                governorates.objects.create(user=user, governorate=gov)

        for city in centers_list:
            if city:
                cities.objects.create(user=user, city=city)
        updated_user = CurrentUserSerializer(user, context={'request': request})
        return Response(updated_user.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]  # لازم يكون مسجل دخول

    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data)
class sendotppassword(APIView) :
    def post(self,request):
        phoneNumber= request.data.get('phoneNumber')
        Newcode = ''.join(random.choices(string.digits, k=6))
        existt = User.objects.filter(phoneNumber=phoneNumber).exists()
        if existt :
            user = User.objects.get(phoneNumber=phoneNumber)
            if User_reset_password.objects.filter(user=user).exists() :
                ocode =User_reset_password.objects.get(user=user)
                if now() - ocode.time_send > timedelta(days=1) or ocode.used:
                    ocode.code = Newcode
                    ocode.time_send= now()
                    ocode.save()
            else:
                User_reset_password.objects.create(user=user, code=Newcode)
            getotp=User_reset_password.objects.get(user=user)
            otp = getotp.code
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            try :
                message = client.messages.create(
                body=f'رمز اعادة تعيين كلمة السر هو   : {otp}',    
                from_='whatsapp:+14155238886',
            
                to=f'whatsapp:+2{phoneNumber}'
                )
                
                return Response ({'message' : 'تم ارسال الرمز بنجاح'}, status=status.HTTP_200_OK)
            except Exception as e:
                #return Response({'message': 'حدث خطأ أثناء إرسال الرمز'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return Response({'message':' تم إرسال . سوف يصل خلال يوم'}, status=status.HTTP_200_OK)

            

        else:
            return Response ({'message': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)



class resetpassword(APIView):
    def post(self,request):
        phoneNumber= request.data.get('phoneNumber')
        code = request.data.get('otp')
        newPassword = request.data.get('newPassword')
        print("Phone Number:", phoneNumber)
        print("Code:", code)
        print("New Password:", newPassword)
        user= User.objects.get(phoneNumber=phoneNumber)
        code1 = User_reset_password.objects.get(user=user)
        if code1.code == code and now() - code1.time_send < timedelta(days=1) and code1.used == False:
            user.set_password(newPassword)
            user.save()
            code1.used = True
            code1.save()
            return Response({'message':'تم تغيير كلمة المرور بنجاح'},status=status.HTTP_200_OK)
        else:
            return Response({'message':'الكود غير صالح'},status=status.HTTP_400_BAD_REQUEST)