"""
Utility functions for accounts app.
"""

import hashlib
import secrets
from django.conf import settings
from twilio.rest import Client
from django.utils.translation import gettext as _


def generate_otp_code():
    """Generate a 6-digit OTP code."""
    return str(secrets.randbelow(900000) + 100000)


def hash_otp_code(code):
    """Hash OTP code with salt."""
    salt = secrets.token_hex(16)
    code_hash = hashlib.pbkdf2_hmac('sha256', code.encode(), salt.encode(), 100000)
    return f"{salt}:{code_hash.hex()}"


def verify_otp_code(code, stored_hash):
    """Verify OTP code against stored hash."""
    try:
        salt, hash_hex = stored_hash.split(':')
        code_hash = hashlib.pbkdf2_hmac('sha256', code.encode(), salt.encode(), 100000)
        return code_hash.hex() == hash_hex
    except ValueError:
        return False


def send_sms_otp(phone_number, otp_code):
    """Send OTP via SMS using Twilio."""
    if not settings.TWILIO_ACCOUNT_SID:
        print(f"SMS OTP for {phone_number}: {otp_code}")  # Development fallback
        return True
    
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=_('Your verification code is: {}. Valid for 10 minutes.').format(otp_code),
            from_=settings.TWILIO_PHONE_NUMBER,
            to=str(phone_number)
        )
        
        return message.sid is not None
    except Exception as e:
        print(f"SMS sending failed: {e}")
        return False


def send_email_otp(email, otp_code):
    """Send OTP via email."""
    from django.core.mail import send_mail
    
    try:
        send_mail(
            subject=_('Your Verification Code'),
            message=_('Your verification code is: {}. Valid for 10 minutes.').format(otp_code),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False