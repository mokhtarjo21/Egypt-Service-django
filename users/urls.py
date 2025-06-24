from .views import *
from django.urls import path , include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
urlpatterns = [
    
    path('check_email', check_email.as_view(), name='check_email'),
    path('check_vendor', check_vendor.as_view(), name='check_vendor'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout', LogoutView.as_view(), name='logout'),
    path ('verify-phone/', ActivationView.as_view(), name='activate'),
    path('send-otp/', send_activation_email, name='active'),
    path ('who/', CurrentUserAPIView.as_view(), name='who'),
    path('verify/', verify.as_view(), name='delete_user'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('login/', CustomTokenObtainPairView.as_view(), name='custom_token_obtain_pair'),
    path('change-password/',userSaveInfo.as_view(), name='user_info'),
    path('update-profile/',update_profile, name='user_update_info'),
    path('all/', all_users.as_view(), name='all_users'),
    path('send-otp-reset-pass/',sendotppassword.as_view(), name='sendforget'),
    path('reset-password/',resetpassword.as_view(), name='resetpassword'),
  
]
