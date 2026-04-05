from django.test import TestCase
from django.conf import settings
from unittest.mock import patch
from apps.payments.paymob import PaymobWallet

class PaymobWalletTests(TestCase):
    
    def setUp(self):
        settings.PAYMOB_HMAC_SECRET = "TEST_SECRET"
    
    def test_verify_hmac_valid(self):
        # 1. Provide mock data from a typical successful webhook payload
        payload = {
            "type": "TRANSACTION",
            "obj": {
                "amount_cents": 15000,
                "created_at": "2024-03-12T10:00:00",
                "currency": "EGP",
                "error_occured": False,
                "has_parent_transaction": False,
                "id": 1234567,
                "integration_id": 987654,
                "is_3d_secure": False,
                "is_auth": False,
                "is_capture": False,
                "is_refunded": False,
                "is_standalone_payment": True,
                "is_voided": False,
                "order": {"id": 888888},
                "owner": 4444,
                "pending": False,
                "source_data": {
                    "pan": "01010101010",
                    "sub_type": "WALLET",
                    "type": "wallet"
                },
                "success": True
            }
        }

        # 2. Re-create the hash using the identical logic
        string_to_hash = (
            "15000" +
            "2024-03-12T10:00:00" +
            "EGP" +
            "false" + # error_occured
            "false" + # has_parent_transaction
            "1234567" +
            "987654" +
            "false" + # is_3d_secure
            "false" + # is_auth
            "false" + # is_capture
            "false" + # is_refunded
            "true" +  # is_standalone_payment
            "false" + # is_voided
            "888888" + # order.id
            "4444" +  # owner
            "false" + # pending
            "01010101010" + # source_data.pan
            "WALLET" + # source_data.sub_type
            "wallet" + # source_data.type
            "true"     # success
        )
        
        import hmac, hashlib
        valid_hmac = hmac.new(
            b"TEST_SECRET", 
            string_to_hash.encode('utf-8'), 
            hashlib.sha512
        ).hexdigest()

        # 3. Assert our method correctly validates it
        is_valid = PaymobWallet.verify_hmac(payload, valid_hmac)
        self.assertTrue(is_valid)
        
    def test_verify_hmac_invalid(self):
        payload = {"obj": {"amount_cents": 1000, "success": True}}
        is_valid = PaymobWallet.verify_hmac(payload, "invalid_hmac_hash123")
        self.assertFalse(is_valid)
