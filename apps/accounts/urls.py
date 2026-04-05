from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='users')

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/2fa/login/', views.TwoFactorLoginView.as_view(), name='2fa-login'),
    path('auth/google/', views.GoogleLoginView.as_view(), name='google-login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # OTP
    path('auth/otp/send/', views.OTPSendView.as_view(), name='otp-send'),
    path('auth/otp/verify/', views.OTPVerifyView.as_view(), name='otp-verify'),
    
    # Password Reset
    path('auth/password/forgot/', views.PasswordResetRequestView.as_view(), name='password-forgot'),
    path('auth/password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile-update'),
    path('profile/id-document/', views.IDDocumentUploadView.as_view(), name='id-document-upload'),
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('profile/change-phone/request/', views.PhoneChangeRequestView.as_view(), name='change-phone-request'),
    path('profile/change-phone/verify/', views.PhoneChangeVerifyView.as_view(), name='change-phone-verify'),
    
    # Router URLs
    path('', include(router.urls)),
    
    # Admin endpoints
    path('admin/users/', views.AdminUserListView.as_view(), name='admin-users-list'),
    path('admin/users/<uuid:user_id>/', views.AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<uuid:user_id>/documents/', views.AdminUserDocumentView.as_view(), name='admin-user-documents'),
    path('admin/users/<uuid:user_id>/status/', views.AdminUserStatusUpdateView.as_view(), name='admin-user-status'),
    
    # Security endpoints
    path('security/2fa/status/', views.TwoFactorStatusView.as_view(), name='2fa-status'),
    path('security/2fa/enable/', views.TwoFactorEnableView.as_view(), name='2fa-enable'),
    path('security/2fa/verify/', views.TwoFactorVerifyView.as_view(), name='2fa-verify'),
    path('security/2fa/disable/', views.TwoFactorDisableView.as_view(), name='2fa-disable'),
    path('security/devices/', views.UserDevicesView.as_view(), name='user-devices'),
    path('security/devices/<str:device_id>/revoke/', views.RevokeDeviceView.as_view(), name='revoke-device'),
    path('security/alerts/', views.SecurityAlertsView.as_view(), name='security-alerts'),
]