"""
Serializers for the payments app.
TODO: Implement payment serializers.
"""

from rest_framework import serializers
from .models import Payment, Wallet, WalletTransaction


class WalletTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for WalletTransaction model.
    """
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'amount', 'transaction_type', 'description', 
            'created_at', 'payment'
        ]


class WalletSerializer(serializers.ModelSerializer):
    """
    Serializer for Wallet model.
    """
    class Meta:
        model = Wallet
        fields = ['balance', 'currency', 'is_frozen']


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model.
    """
    class Meta:
        model = Payment
        fields = '__all__'