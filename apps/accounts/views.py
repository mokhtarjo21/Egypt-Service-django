"""
Views for the accounts app.
"""

import hashlib
import secrets
from datetime import timedelta
from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
import pyotp
import qrcode
import io
import base64
from apps.notifications.utils import send_notification_if_enabled

from .models import User, OTPCode, LoginAttempt, UserDocument, AdminAction, TOTPSecret, UserDevice, SecurityAlert
from .serializers import (
    UserSerializer, 
    RegisterSerializer,
    LoginSerializer,
    GoogleLoginSerializer,
    ProfileUpdateSerializer,
    OTPSendSerializer,
    OTPVerifySerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    IDDocumentUploadSerializer,
    ChangePasswordSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    GoogleLoginSerializer,
    PhoneChangeRequestSerializer,
    PhoneChangeVerifySerializer
)
from .utils import send_sms_otp, generate_otp_code, hash_otp_code, verify_otp_code
from .google_auth import verify_google_token
from django.contrib.contenttypes.models import ContentType


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST'), name='post')
class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send OTP for phone verification
        otp_code = generate_otp_code()
        otp_hash = hash_otp_code(otp_code)
        
        OTPCode.objects.create(
            user=user,
            code_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # Send SMS
        send_sms_otp(user.phone_number, otp_code)
        
        return Response({
            'message': _('Registration successful. Please verify your phone number.'),
            'user_id': str(user.id),
            'phone_number': str(user.phone_number)
        }, status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST'), name='post')
class LoginView(generics.GenericAPIView):
    """
    User login endpoint.
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        password = serializer.validated_data['password']
        
        # Log login attempt
        ip_address = request.META.get('REMOTE_ADDR','')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        try:
            user = User.objects.get(phone_number=phone_number)
            
            if user.check_password(password):
                if not user.is_phone_verified:
                    LoginAttempt.objects.create(
                        phone_number=phone_number,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        failure_reason='Phone not verified'
                    )
                    return Response({
                        'error': _('Phone number not verified')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if user.status in ['suspended', 'blocked']:
                    LoginAttempt.objects.create(
                        phone_number=phone_number,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        failure_reason=f'Account {user.status}'
                    )
                    return Response({
                        'error': _('Account is suspended or blocked')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check if 2FA is enabled
                try:
                    totp_secret = TOTPSecret.objects.get(user=user, is_verified=True)
                    # 2FA is enabled — return a challenge token instead of real tokens
                    from django.core import signing
                    temp_token = signing.dumps(
                        {'user_id': str(user.id)},
                        salt='2fa_login',
                        compress=True
                    )
                    return Response({
                        'requires_2fa': True,
                        'temp_token': temp_token,
                    }, status=status.HTTP_200_OK)
                except TOTPSecret.DoesNotExist:
                    pass  # 2FA not enabled, proceed with normal login
                
                # Successful login (no 2FA)
                LoginAttempt.objects.create(
                    phone_number=phone_number,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=True
                )
                
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })
            else:
                LoginAttempt.objects.create(
                    phone_number=phone_number,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason='Invalid password'
                )
        except User.DoesNotExist:
            LoginAttempt.objects.create(
                phone_number=phone_number,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason='User not found'
            )
        
        return Response({
            'error': _('Invalid credentials')
        }, status=status.HTTP_400_BAD_REQUEST)


class TwoFactorLoginView(generics.GenericAPIView):
    """
    Complete login when 2FA is enabled.
    Accepts the temp_token from LoginView and a TOTP code, returns real JWT tokens.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        from django.core import signing
        temp_token = request.data.get('temp_token')
        code = request.data.get('code')

        if not temp_token or not code:
            return Response({'error': 'temp_token and code are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = signing.loads(temp_token, salt='2fa_login', max_age=300)  # 5-minute expiry
            user = User.objects.get(id=data['user_id'])
        except signing.SignatureExpired:
            return Response({'error': 'Session expired. Please log in again.'}, status=status.HTTP_400_BAD_REQUEST)
        except (signing.BadSignature, User.DoesNotExist, KeyError):
            return Response({'error': 'Invalid session token.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            totp_secret = TOTPSecret.objects.get(user=user, is_verified=True)
            secret = totp_secret.decrypt_secret()
            totp = pyotp.TOTP(secret)

            if totp.verify(str(code), valid_window=1):
                totp_secret.last_used = timezone.now()
                totp_secret.save(update_fields=['last_used'])

                ip_address = request.META.get('REMOTE_ADDR', '')
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                LoginAttempt.objects.create(
                    phone_number=user.phone_number,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=True
                )

                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })

            # Check backup codes
            code_hash = hashlib.sha256(code.upper().encode()).hexdigest()
            if code_hash in totp_secret.backup_codes:
                totp_secret.backup_codes = [c for c in totp_secret.backup_codes if c != code_hash]
                totp_secret.save()

                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })

            return Response({'error': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)

        except TOTPSecret.DoesNotExist:
            return Response({'error': '2FA not configured'}, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(generics.GenericAPIView):
    """
    Google authentication endpoint (login and signup).
    - New users: created with status='pending' and directed to upload ID documents.
    - Existing users: logged in normally (status unchanged).
    """
    serializer_class = GoogleLoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        id_token = serializer.validated_data['id_token']
        role = serializer.validated_data.get('role', 'user')
        
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        try:
            # Verify the token and get the user's Google info
            idinfo = verify_google_token(id_token)
            email = idinfo.get('email')
            full_name = idinfo.get('name', '')
            picture = idinfo.get('picture', '')  # Google profile photo URL
            
            if not email:
                return Response({'error': _('Email not provided by Google')}, status=status.HTTP_400_BAD_REQUEST)

            # Check if user exists
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'full_name': full_name,
                    # Generate a temporary unique phone placeholder for Google users.
                    # User must update it from their profile later.
                    'phone_number': f"+20100{secrets.randbelow(8999999) + 1000000}",
                    'is_phone_verified': False,
                    'email_verified': idinfo.get('email_verified', False), 
                    # New Google users start as 'pending' — they must upload
                    # their national ID and get approved by an admin before
                    # they can publish services. This matches the platform's
                    # identity-verification policy.
                    'status': 'rejected',
                    'role': role
                }
            )

            if created:
                # Set unusable password since they login via Google
                user.set_unusable_password()
                # Save Google avatar URL as bio placeholder so frontend can show it
                # (actual avatar upload is via the profile page)
                if picture:
                    user.bio = user.bio or ''  # keep existing bio
                user.save()
            
            if user.status in ['suspended', 'blocked']:
                LoginAttempt.objects.create(
                    phone_number=str(user.phone_number),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason=f'Account {user.status}'
                )
                return Response({'error': _('Account is suspended or blocked')}, status=status.HTTP_400_BAD_REQUEST)

            # Successful login
            LoginAttempt.objects.create(
                phone_number=str(user.phone_number),
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            
            refresh = RefreshToken.for_user(user)

            # Tell the frontend whether this user still needs to submit ID docs
            needs_id_verification = (
                user.status == 'pending' and
                not user.id_document and
                not user.documents.filter(status__in=['pending', 'approved']).exists()
            )

            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'is_new_user': created,
                'needs_id_verification': needs_id_verification,
                'google_picture': picture,  # Frontend can use this to pre-fill avatar
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': _('Authentication failed')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(generics.GenericAPIView):
    """
    User logout endpoint.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Logout failed: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ratelimit(key='ip', rate='5/h', method='POST'), name='post')
class OTPSendView(generics.GenericAPIView):
    """
    Send OTP code.
    """
    serializer_class = OTPSendSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        purpose = serializer.validated_data['purpose']
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({
                'error': _('User not found')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check rate limiting
        recent_otps = OTPCode.objects.filter(
            user=user,
            purpose=purpose,
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_otps >= 5:
            return Response({
                'error': _('Too many OTP requests. Please try again later.')
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Generate and send OTP
        otp_code = generate_otp_code()
        otp_hash = hash_otp_code(otp_code)
        
        OTPCode.objects.create(
            user=user,
            code_hash=otp_hash,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        send_sms_otp(phone_number, otp_code)
        
        return Response({
            'message': _('OTP sent successfully')
        })


class OTPVerifyView(generics.GenericAPIView):
    """
    Verify OTP code.
    """
    serializer_class = OTPVerifySerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']
        purpose = serializer.validated_data['purpose']
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({
                'error': _('User not found')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Find valid OTP
        otp = OTPCode.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if not otp:
            return Response({
                'error': _('Invalid or expired OTP')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify code
        if verify_otp_code(code, otp.code_hash):
            otp.is_used = True
            otp.save()
            
            # Update user verification status
            if purpose == 'registration':
                user.is_phone_verified = True
                user.save()
            
            # Generate tokens for successful verification
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': _('OTP verified successfully'),
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        else:
            otp.attempts += 1
            otp.save()
            
            return Response({
                'error': _('Invalid OTP code')
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(generics.GenericAPIView):
    """
    Request password reset.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            # Don't reveal if user exists
            return Response({
                'message': _('If the phone number exists, you will receive an OTP')
            })
        
        # Generate and send OTP
        otp_code = generate_otp_code()
        otp_hash = hash_otp_code(otp_code)
        
        OTPCode.objects.create(
            user=user,
            code_hash=otp_hash,
            purpose='password_reset',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        send_sms_otp(phone_number, otp_code)
        
        return Response({
            'message': _('If the phone number exists, you will receive an OTP')
        })


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Confirm password reset.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({
                'error': _('User not found')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Find valid OTP
        otp = OTPCode.objects.filter(
            user=user,
            purpose='password_reset',
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if not otp or not verify_otp_code(code, otp.code_hash):
            return Response({
                'error': _('Invalid or expired OTP')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset password
        user.set_password(new_password)
        user.save()
        
        otp.is_used = True
        otp.save()
        
        return Response({
            'message': _('Password reset successfully')
        })


class PhoneChangeRequestView(generics.GenericAPIView):
    """
    Request a phone number change (for authenticated users).
    """
    serializer_class = PhoneChangeRequestSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_phone_number = serializer.validated_data['new_phone_number']
        user = request.user
        
        # Check rate limiting for OTP
        recent_otps = OTPCode.objects.filter(
            user=user,
            purpose='phone_change',
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_otps >= 5:
            return Response({
                'error': _('Too many OTP requests. Please try again later.')
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Generate and send OTP to the new number
        otp_code = generate_otp_code()
        otp_hash = hash_otp_code(otp_code)
        
        OTPCode.objects.create(
            user=user,
            code_hash=otp_hash,
            purpose='phone_change',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        send_sms_otp(new_phone_number, otp_code)
        
        return Response({
            'message': _('OTP sent to the new phone number successfully')
        })


class PhoneChangeVerifyView(generics.GenericAPIView):
    """
    Verify the new phone number with the OTP code.
    """
    serializer_class = PhoneChangeVerifySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_phone_number = serializer.validated_data['new_phone_number']
        code = serializer.validated_data['code']
        user = request.user
        
        # Find valid OTP for phone change
        otp = OTPCode.objects.filter(
            user=user,
            purpose='phone_change',
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if not otp or not verify_otp_code(code, otp.code_hash):
            return Response({
                'error': _('Invalid or expired OTP')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark as used and update user phone
        otp.is_used = True
        otp.save()
        
        user.phone_number = new_phone_number
        user.save()
        
        return Response({
            'message': _('Phone number updated successfully'),
            'user': UserSerializer(user).data
        })


class ProfileView(generics.RetrieveAPIView):
    """
    Get user profile.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ProfileUpdateView(generics.UpdateAPIView):
    """
    Update user profile.
    """
    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class IDDocumentUploadView(generics.GenericAPIView):
    """
    Upload ID documents.
    Only allowed for users with 'pending' or 'rejected' status.
    """
    serializer_class = IDDocumentUploadSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Block upload for already-verified users or suspended/blocked users
        if user.status == 'verified':
            return Response(
                {'error': _('حسابك مفعّل بالفعل ولا يمكن إعادة رفع المستندات.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        if user.status in ['suspended', 'blocked']:
            return Response(
                {'error': _('حسابك موقوف. يرجى التواصل مع الدعم.')},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.id_document = serializer.validated_data['id_document']
        if 'id_document_back' in serializer.validated_data:
            user.id_document_back = serializer.validated_data['id_document_back']

        # Reset status to pending for re-review
        user.status = 'pending'
        user.rejection_reason = ''
        user.save()

        return Response({
            'message': _('تم رفع المستندات بنجاح. سيتم مراجعة حسابك قريباً.'),
            'user': UserSerializer(user).data
        })


class ChangePasswordView(generics.GenericAPIView):
    """
    Change user password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': _('Password changed successfully')
        })


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user profiles.
    """
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer

    def get_permissions(self):
        """Allow public access to profile retrieval and stats."""
        if self.action in ['retrieve', 'stats', 'services']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def sessions(self, request):
        """
        Get user sessions.
        """
        sessions = request.user.sessions.filter(is_active=True)
        return Response([
            {
                'id': session.id,
                'ip_address': session.ip_address,
                'user_agent': session.user_agent[:100],
                'last_activity': session.last_activity,
                'is_current': session.session_key == request.session.session_key
            }
            for session in sessions
        ])

    @action(detail=False, methods=['post'])
    def logout_all_sessions(self, request):
        """
        Logout from all sessions.
        """
        request.user.sessions.update(is_active=False)
        return Response({'message': _('Logged out from all sessions')})

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def stats(self, request, pk=None):
        """
        Public provider stats: avg rating, completed bookings, services count, reviews.
        """
        from django.db.models import Avg, Count
        try:
            user = User.objects.get(pk=pk, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Completed bookings as provider
        completed_bookings = 0
        try:
            from apps.bookings.models import Booking
            completed_bookings = Booking.objects.filter(
                provider=user, status='completed'
            ).count()
        except Exception:
            pass

        # Average rating & review count from reviews on provider's services
        avg_rating = 0
        review_count = 0
        try:
            from apps.reviews.models import Review
            agg = Review.objects.filter(
                service__owner=user, status='approved'
            ).aggregate(avg=Avg('rating'), cnt=Count('id'))
            avg_rating = round(agg['avg'] or 0, 1)
            review_count = agg['cnt'] or 0
        except Exception:
            pass

        # Active services count
        services_count = 0
        try:
            from apps.services.models import Service
            services_count = Service.objects.filter(
                owner=user, status='approved', is_active=True
            ).count()
        except Exception:
            pass

        return Response({
            'completed_bookings': completed_bookings,
            'avg_rating': avg_rating,
            'review_count': review_count,
            'services_count': services_count,
            'is_verified': user.status == 'verified',
            'member_since': user.date_joined,
        })

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def services(self, request, pk=None):
        """
        Public list of provider's active approved services.
        """
        try:
            user = User.objects.get(pk=pk, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            from apps.services.models import Service
            from apps.services.serializers import ServiceListSerializer
            services = Service.objects.filter(
                owner=user, status='approved', is_active=True
            ).order_by('-created_at')[:6]
            from apps.services.serializers import ServiceSerializer
            return Response(ServiceSerializer(services, many=True, context={'request': request}).data)
        except Exception as e:
            return Response([])

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def reviews(self, request, pk=None):
        """
        Public list of approved reviews for a provider.
        """
        try:
            user = User.objects.get(pk=pk, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            from apps.reviews.models import Review
            reviews_qs = Review.objects.filter(
                service__owner=user, status='approved'
            ).select_related('reviewer', 'service').order_by('-created_at')[:5]

            data = []
            for r in reviews_qs:
                data.append({
                    'id': str(r.id),
                    'rating': r.rating,
                    'title': r.title,
                    'comment': r.comment,
                    'created_at': r.created_at,
                    'reviewer_name': r.reviewer.full_name,
                    'reviewer_avatar': request.build_absolute_uri(r.reviewer.avatar.url) if r.reviewer.avatar else None,
                    'service_title': r.service.title_ar,
                })
            return Response(data)
        except Exception:
            return Response([])




# Admin Views
class AdminUserListView(generics.ListAPIView):
    """
    Admin view to list all users.
    """
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['full_name', 'phone_number', 'email']
    ordering_fields = ['date_joined', 'last_login', 'full_name']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        if not self.request.user.role == 'admin':
            return User.objects.none()
        return User.objects.all()


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    """
    Admin view to get/update user details.
    """
    serializer_class = AdminUserUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        if not self.request.user.role == 'admin':
            return User.objects.none()
        return User.objects.all()
    
    def perform_update(self, serializer):
        user = serializer.save()

        # Log admin action (GenericFK requires content_type + object_id)
        from django.contrib.contenttypes.models import ContentType
        AdminAction.objects.create(
            admin=self.request.user,
            action_type='user_verify',
            target_user=user,
            content_type=ContentType.objects.get_for_model(user),
            object_id=user.pk,
            reason=f"Updated user status to {user.status}",
            ip_address=self.request.META.get('REMOTE_ADDR', ''),
        )


class AdminUserDocumentView(generics.RetrieveAPIView):
    """
    Admin view to view user documents.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        if not request.user.role == 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(id=user_id)
            documents = user.documents.all()
            
            return Response({
                'user': AdminUserSerializer(user).data,
                'documents': [
                    {
                        'id': doc.id,
                        'document_type': doc.document_type,
                        'status': doc.status,
                        'rejection_reason': doc.rejection_reason,
                        'created_at': doc.created_at,
                        'verified_at': doc.verified_at,
                        # Note: Document URLs should be signed URLs in production
                        'document_front_url': doc.document_front.url if doc.document_front else None,
                        'document_back_url': doc.document_back.url if doc.document_back else None,
                    }
                    for doc in documents
                ]
            })
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(ratelimit(key='user', rate='10/m', method='POST'), name='post')
class AdminUserStatusUpdateView(generics.GenericAPIView):
    """
    Admin view to update user status.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id):
        if not request.user.role == 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(id=user_id)
            new_status = request.data.get('status')
            reason = request.data.get('reason', '')
            
            if new_status not in ['pending', 'verified', 'rejected', 'suspended', 'blocked']:
                return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
            
            old_status = user.status
            user.status = new_status
            if new_status == 'rejected':
                user.rejection_reason = reason
            user.save()
            
            # Log admin action (GenericFK requires content_type + object_id)
            from django.contrib.contenttypes.models import ContentType
            action_type_map = {
                'verified': 'user_verify',
                'rejected': 'user_reject',
                'suspended': 'user_suspend',
                'blocked': 'user_block',
                'pending': 'user_verify',
            }
            action_type = action_type_map.get(new_status, 'user_verify')
            AdminAction.objects.create(
                admin=request.user,
                action_type=action_type,
                target_user=user,
                content_type=ContentType.objects.get_for_model(user),
                object_id=user.pk,
                reason=reason,
                notes=f"Status changed from {old_status} to {new_status}",
                ip_address=request.META.get('REMOTE_ADDR', ''),
            )
            
            # Notify user
            if new_status == 'active':
                send_notification_if_enabled(
                    recipient=user,
                    notification_type='account_verified',
                    title_ar='تم تفعيل حسابك',
                    title_en='Account Activated',
                    message_ar='تم مراجعة وثائقك وتفعيل حسابك بنجاح. يمكنك الآن استخدام كافة ميزات المنصة.',
                    message_en='Your documents have been reviewed and your account is now active.',
                    related_object=user
                )
            elif new_status == 'rejected':
                send_notification_if_enabled(
                    recipient=user,
                    notification_type='account_verified',
                    title_ar='تحديث حالة الحساب',
                    title_en='Account Status Update',
                    message_ar=f'نعتذر، لم يتم قبول طلب تفعيل حسابك. السبب: {reason}',
                    message_en=f'Sorry, your account activation request was not accepted. Reason: {reason}',
                    related_object=user
                )
            
            return Response({
                'message': f'User status updated to {new_status}',
                'user': AdminUserSerializer(user).data
            })
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


# Security Views
class TwoFactorStatusView(generics.GenericAPIView):
    """
    Check 2FA status.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            totp_secret = TOTPSecret.objects.get(user=request.user)
            return Response({
                'enabled': totp_secret.is_verified,
                'last_used': totp_secret.last_used
            })
        except TOTPSecret.DoesNotExist:
            return Response({'enabled': False})


class TwoFactorEnableView(generics.GenericAPIView):
    """
    Enable 2FA and generate QR code.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Generate TOTP secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Create QR code
        provisioning_uri = totp.provisioning_uri(
            name=str(user.phone_number),
            issuer_name="Egyptian Service Marketplace"
        )
        
        # Store encrypted secret
        totp_secret, created = TOTPSecret.objects.get_or_create(user=user)
        totp_secret.encrypt_secret(secret)
        totp_secret.is_verified = False
        totp_secret.save()
        
        return Response({
            'qr_code_url': provisioning_uri,
            'secret': secret  # For manual entry
        })


class TwoFactorVerifyView(generics.GenericAPIView):
    """
    Verify 2FA setup.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        code = request.data.get('code')
        
        try:
            totp_secret = TOTPSecret.objects.get(user=user)
            secret = totp_secret.decrypt_secret()
            totp = pyotp.TOTP(secret)
            
            # valid_window=1 allows codes ±30 seconds to handle clock drift
            if totp.verify(str(code), valid_window=1):
                totp_secret.is_verified = True
                backup_codes = totp_secret.generate_backup_codes()
                totp_secret.save()
                
                return Response({
                    'success': True,
                    'backup_codes': backup_codes
                })
            
            # Check if it's a backup code
            code_hash = hashlib.sha256(code.upper().encode()).hexdigest()
            if code_hash in totp_secret.backup_codes:
                # Remove used backup code
                totp_secret.backup_codes = [c for c in totp_secret.backup_codes if c != code_hash]
                totp_secret.save()
                return Response({
                    'success': True,
                    'message': 'Backup code used successfully'
                })
            
            return Response({
                'error': 'Invalid verification code'
            }, status=status.HTTP_400_BAD_REQUEST)
                
        except TOTPSecret.DoesNotExist:
            return Response({
                'error': '2FA not initialized'
            }, status=status.HTTP_400_BAD_REQUEST)



class TwoFactorDisableView(generics.GenericAPIView):
    """
    Disable 2FA.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        try:
            totp_secret = TOTPSecret.objects.get(user=user)
            totp_secret.delete()
            
            # Create security alert
            SecurityAlert.objects.create(
                user=user,
                alert_type='2fa_disabled',
                message='تم إلغاء تفعيل المصادقة الثنائية',
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({'success': True})
        except TOTPSecret.DoesNotExist:
            return Response({
                'error': '2FA not enabled'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserDevicesView(generics.ListAPIView):
    """
    List user devices and sessions.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        devices = UserDevice.objects.filter(user=request.user, is_active=True)
        
        device_data = []
        for device in devices:
            device_data.append({
                'id': device.id,
                'device_name': device.device_name,
                'device_fingerprint': device.device_fingerprint,
                'ip_address': device.ip_address,
                'location': device.location,
                'last_seen': device.last_seen,
                'is_trusted': device.is_trusted,
                'is_current': device.device_fingerprint == request.META.get('HTTP_X_DEVICE_FINGERPRINT', '')
            })
        
        return Response(device_data)


class RevokeDeviceView(generics.GenericAPIView):
    """
    Revoke device access.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, device_id):
        try:
            device = UserDevice.objects.get(id=device_id, user=request.user)
            device.is_active = False
            device.save()
            
            return Response({'success': True})
        except UserDevice.DoesNotExist:
            return Response({
                'error': 'Device not found'
            }, status=status.HTTP_404_NOT_FOUND)


class SecurityAlertsView(generics.ListAPIView):
    """
    List security alerts for user.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        alerts = SecurityAlert.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-created_at')[:20]
        
        alert_data = []
        for alert in alerts:
            alert_data.append({
                'id': alert.id,
                'alert_type': alert.alert_type,
                'message': alert.message,
                'ip_address': alert.ip_address,
                'created_at': alert.created_at,
                'is_resolved': alert.is_resolved
            })
        
        return Response(alert_data)