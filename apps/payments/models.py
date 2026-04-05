"""
Payment models for Egyptian Service Marketplace.
TODO: Implement full payment system with Egyptian payment gateways.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

User = get_user_model()


class Payment(BaseModel):
    """
    Placeholder payment model.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('booking', _('Booking Payment')),
        ('subscription', _('Subscription Plan')),
    ]

    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('Booking')
    )
    paymob_order_id = models.CharField(_('Paymob Order ID'), max_length=100, blank=True)
    mobile_number = models.CharField(_('Mobile Number'), max_length=20, blank=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('User')
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=10,
        decimal_places=2
    )
    currency = models.CharField(_('Currency'), max_length=3, default='EGP')
    status = models.CharField(
        _('Status'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_type = models.CharField(
        _('Payment Type'),
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='booking'
    )
    subscription_plan = models.ForeignKey(
        'subscriptions.SubscriptionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('Subscription Plan')
    )
    payment_method = models.CharField(_('Payment method'), max_length=50)
    transaction_id = models.CharField(_('Transaction ID'), max_length=100, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.amount} {self.currency}"

class Wallet(BaseModel):
    """
    User wallet for tracking balances (mainly for providers).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name=_('User')
    )
    balance = models.DecimalField(
        _('Balance'),
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    currency = models.CharField(_('Currency'), max_length=3, default='EGP')
    is_frozen = models.BooleanField(_('Is Frozen'), default=False)

    class Meta:
        verbose_name = _('Wallet')
        verbose_name_plural = _('Wallets')

    def __str__(self):
        return f"{self.user.full_name}'s Wallet - {self.balance} {self.currency}"

class WalletTransaction(BaseModel):
    """
    Transactions recorded against a wallet.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('credit', _('Credit (Earnings/Deposit)')),
        ('debit', _('Debit (Withdrawal/Fee)')),
    ]

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('Wallet')
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=12,
        decimal_places=2
    )
    transaction_type = models.CharField(
        _('Type'),
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES
    )
    description = models.TextField(_('Description'), blank=True)
    
    # Relationships to other objects
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions',
        verbose_name=_('Related Payment')
    )
    
    class Meta:
        verbose_name = _('Wallet Transaction')
        verbose_name_plural = _('Wallet Transactions')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type.upper()} {self.amount} - {self.wallet.user.full_name}"