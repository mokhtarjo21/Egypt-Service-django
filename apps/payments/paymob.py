import requests
import hmac
import hashlib
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class PaymobWallet:
    """
    Utility class to handle Paymob API calls for Vodafone Cash.
    """
    BASE_URL = "https://accept.paymob.com/api"

    @classmethod
    def get_auth_token(cls) -> str:
        """Step 1: Get authentication token."""
        url = f"{cls.BASE_URL}/auth/tokens"
        payload = {"api_key": settings.PAYMOB_API_KEY}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get('token')
        except Exception as e:
            logger.error(f"Paymob Auth Auth returned error: {e}")
            raise

    @classmethod
    def create_order(cls, auth_token: str, amount_cents: int, merchant_order_id: str, items: list = None) -> str:
        """Step 2: Order Registration."""
        url = f"{cls.BASE_URL}/ecommerce/orders"
        payload = {
            "auth_token": auth_token,
            "delivery_needed": "false",
            "amount_cents": str(amount_cents),
            "currency": "EGP",
            "merchant_order_id": merchant_order_id,
            "items": items or []
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return str(response.json().get('id'))
        except Exception as e:
            logger.error(f"Paymob Create Order returned error: {e}")
            raise

    @classmethod
    def get_payment_key(cls, auth_token: str, order_id: str, amount_cents: int, billing_data: dict) -> str:
        """Step 3: Payment Key Request."""
        url = f"{cls.BASE_URL}/acceptance/payment_keys"
        payload = {
            "auth_token": auth_token,
            "amount_cents": str(amount_cents),
            "expiration": 3600,
            "order_id": order_id,
            "billing_data": {
                "apartment": billing_data.get('apartment', 'NA'),
                "email": billing_data.get('email', 'NA'),
                "floor": billing_data.get('floor', 'NA'),
                "first_name": billing_data.get('first_name', 'NA'),
                "street": billing_data.get('street', 'NA'),
                "building": billing_data.get('building', 'NA'),
                "phone_number": billing_data.get('phone_number', 'NA'),
                "shipping_method": "NA",
                "postal_code": "NA",
                "city": billing_data.get('city', 'NA'),
                "country": "EG",
                "last_name": billing_data.get('last_name', 'NA'),
                "state": billing_data.get('state', 'NA')
            },
            "currency": "EGP",
            "integration_id": settings.PAYMOB_INTEGRATION_ID_VODAFONE_CASH
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get('token')
        except Exception as e:
            logger.error(f"Paymob Payment Key returned error: {e}")
            raise

    @classmethod
    def get_wallet_payment_url(cls, payment_key: str, wallet_mobile_number: str) -> str:
        """Step 4: Request Vodafone Cash Payment URL."""
        url = f"{cls.BASE_URL}/acceptance/payments/pay"
        payload = {
            "source": {
                "identifier": wallet_mobile_number,
                "subtype": "WALLET"
            },
            "payment_token": payment_key
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get('redirect_url')
        except Exception as e:
            logger.error(f"Paymob Wallet URL returned error: {e}")
            raise

    @classmethod
    def verify_hmac(cls, data: dict, received_hmac: str) -> bool:
        """Verify HMAC signature for webhook calls."""
        if not settings.PAYMOB_HMAC_SECRET:
            return False

        # Extract values in the specific order defined by Paymob
        keys_to_hash = [
            'amount_cents', 'created_at', 'currency', 'error_occured',
            'has_parent_transaction', 'id', 'integration_id', 'is_3d_secure',
            'is_auth', 'is_capture', 'is_refunded', 'is_standalone_payment',
            'is_voided', 'order.id', 'owner', 'pending',
            'source_data.pan', 'source_data.sub_type', 'source_data.type', 'success'
        ]

        # Construct the string to hash
        string_to_hash = ""
        obj = data.get('obj', {})
        for key in keys_to_hash:
            if '.' in key:
                parts = key.split('.')
                val = obj
                for p in parts:
                    val = val.get(p, '')
                    if not isinstance(val, dict):
                        break
            else:
                val = obj.get(key, '')
            
            # Paymob expects boolean values to be properly str-ed lower case or exact representation depending
            # Typically python True becomes "True", paymob expects "true"
            if isinstance(val, bool):
                val = str(val).lower()
            
            string_to_hash += str(val)

        # Hash it
        hmac_secret = settings.PAYMOB_HMAC_SECRET.encode('utf-8')
        calculated_hmac = hmac.new(
            hmac_secret, 
            string_to_hash.encode('utf-8'), 
            hashlib.sha512
        ).hexdigest()

        return calculated_hmac == received_hmac

