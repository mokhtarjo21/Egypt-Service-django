"""
Views for the payments app.
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
import uuid

from .models import Payment, Wallet, WalletTransaction
from apps.bookings.models import Booking
from apps.subscriptions.models import SubscriptionPlan, Subscription, SubscriptionUsage
from .paymob import PaymobWallet
from .serializers import PaymentSerializer, WalletSerializer, WalletTransactionSerializer
from apps.notifications.utils import send_notification_if_enabled
import logging

logger = logging.getLogger(__name__)

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for payments.
    """
    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user, is_active=True)

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user wallet and transactions.
    """
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get current balance."""
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get transaction history."""
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        transactions = wallet.transactions.all()
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = WalletTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Request a withdrawal from the wallet."""
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        if wallet.is_frozen:
            return Response(
                {'detail': 'محفظتك مجمدة. يرجى التواصل مع الدعم.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = float(request.data.get('amount', 0))
        except (TypeError, ValueError):
            return Response({'detail': 'المبلغ غير صحيح.'}, status=status.HTTP_400_BAD_REQUEST)

        if amount < 100:
            return Response(
                {'detail': 'الحد الأدنى للسحب هو 100 جنيه.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from decimal import Decimal
        if Decimal(str(amount)) > wallet.balance:
            return Response(
                {'detail': 'رصيدك غير كافٍ لإتمام عملية السحب.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        mobile_number = request.data.get('mobile_number', '').strip()
        if not mobile_number:
            return Response({'detail': 'رقم المحفظة مطلوب.'}, status=status.HTTP_400_BAD_REQUEST)

        # Deduct from wallet
        wallet.balance -= Decimal(str(amount))
        wallet.save()

        # Record the transaction
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='debit',
            description=f'سحب رصيد إلى محفظة {mobile_number}'
        )

        # Notify user
        try:
            send_notification_if_enabled(
                recipient=request.user,
                notification_type='payment',
                title_ar='تم طلب السحب',
                title_en='Withdrawal Requested',
                message_ar=f'تم خصم {amount} جنيه من محفظتك كطلب سحب إلى {mobile_number}. سيتم المعالجة خلال 24 ساعة.',
                message_en=f'Withdrawal of {amount} EGP to {mobile_number} has been requested. Processing within 24 hours.',
            )
        except Exception:
            pass

        serializer = self.get_serializer(wallet)
        return Response({
            'detail': f'تم طلب سحب {amount} جنيه بنجاح. سيصلك المبلغ خلال 24 ساعة.',
            'wallet': serializer.data,
        }, status=status.HTTP_200_OK)

class PaymobCheckoutView(APIView):
    """
    Initiate a Vodafone Cash payment via Paymob.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        booking_id = request.data.get('booking_id')
        mobile_number = request.data.get('mobile_number')

        if not booking_id or not mobile_number:
            return Response(
                {"detail": "Booking ID and Mobile Number are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)

        if booking.status != 'confirmed':
            return Response(
                {"detail": "Only confirmed bookings can be paid for."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if booking.is_paid:
            return Response(
                {"detail": "Booking is already paid."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1. Auth
            auth_token = PaymobWallet.get_auth_token()

            # 2. Order
            amount_cents = int(booking.total_amount * 100)
            merchant_order_id = f"{booking.booking_number}-{uuid.uuid4().hex[:6]}"
            order_id = PaymobWallet.create_order(
                auth_token, amount_cents, merchant_order_id
            )

            # 3. Payment Key
            billing_data = {
                "first_name": request.user.first_name or "NA",
                "last_name": request.user.last_name or "NA",
                "email": request.user.email or "NA",
                "phone_number": request.user.phone_number or "NA",
                "city": "Cairo", # Or get from booking
            }
            payment_key = PaymobWallet.get_payment_key(
                auth_token, order_id, amount_cents, billing_data
            )

            # 4. Get wallet payment iframe URL
            redirect_url = PaymobWallet.get_wallet_payment_url(
                payment_key, mobile_number
            )

            # Create pending Payment record
            Payment.objects.create(
                user=request.user,
                booking=booking,
                amount=booking.total_amount,
                currency='EGP',
                status='pending',
                payment_method='vodafone_cash',
                transaction_id=merchant_order_id,
                paymob_order_id=order_id,
                mobile_number=mobile_number
            )

            return Response({"redirect_url": redirect_url}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error initiating Paymob payment: {str(e)}")
            return Response(
                {"detail": "An error occurred while communicating with the payment gateway."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymobSubscriptionCheckoutView(APIView):
    """
    Initiate a subscription payment via Paymob.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        plan_id = request.data.get('plan_id')
        mobile_number = request.data.get('mobile_number')

        if not plan_id or not mobile_number:
            return Response(
                {"detail": "Plan ID and Mobile Number are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        try:
            # 1. Auth
            auth_token = PaymobWallet.get_auth_token()

            # 2. Order
            amount_cents = int(plan.price * 100)
            merchant_order_id = f"SUB-{plan.plan_type}-{uuid.uuid4().hex[:6]}"
            order_id = PaymobWallet.create_order(
                auth_token, amount_cents, merchant_order_id
            )

            # 3. Payment Key
            billing_data = {
                "first_name": request.user.first_name or "NA",
                "last_name": request.user.last_name or "NA",
                "email": request.user.email or "NA",
                "phone_number": request.user.phone_number or "NA",
                "city": "Cairo",
            }
            payment_key = PaymobWallet.get_payment_key(
                auth_token, order_id, amount_cents, billing_data
            )

            # 4. Get wallet payment iframe URL
            redirect_url = PaymobWallet.get_wallet_payment_url(
                payment_key, mobile_number
            )

            # Create pending Payment record
            Payment.objects.create(
                user=request.user,
                subscription_plan=plan,
                payment_type='subscription',
                amount=plan.price,
                currency='EGP',
                status='pending',
                payment_method='vodafone_cash',
                transaction_id=merchant_order_id,
                paymob_order_id=order_id,
                mobile_number=mobile_number
            )

            return Response({"redirect_url": redirect_url}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error initiating Paymob subscription payment: {str(e)}")
            return Response(
                {"detail": "An error occurred while communicating with the payment gateway."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymobWebhookView(APIView):
    """
    Webhook handler for Paymob transactions.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data
        received_hmac = request.query_params.get('hmac')

        # Verify HMAC
        if not received_hmac or not PaymobWallet.verify_hmac(data, received_hmac):
            logger.warning("Invalid Paymob HMAC received.")
            return Response({"detail": "Invalid HMAC signature"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Process webhook
        obj = data.get('obj', {})
        order_id = str(obj.get('order', {}).get('id'))
        success = obj.get('success', False)
        
        try:
            payment = Payment.objects.get(paymob_order_id=order_id)
            
            if success:
                payment.status = 'completed'
                payment.save()
                
                from django.utils import timezone
                
                if payment.payment_type == 'booking' and payment.booking:
                    payment.booking.is_paid = True
                    payment.booking.save()
                    
                    # Credit provider wallet
                    if payment.booking.provider:
                        provider_wallet, _ = Wallet.objects.get_or_create(user=payment.booking.provider)
                        provider_wallet.balance += payment.amount
                        provider_wallet.save()
                        
                        WalletTransaction.objects.create(
                            wallet=provider_wallet,
                            amount=payment.amount,
                            transaction_type='credit',
                            description=f'Earnings for booking #{payment.booking.booking_number}',
                            payment=payment
                        )
                
                elif payment.payment_type == 'subscription' and payment.subscription_plan:
                    # Deactivate old active subscriptions
                    Subscription.objects.filter(user=payment.user, status='active').update(
                        status='canceled',
                        canceled_at=timezone.now()
                    )

                    # Create new subscription
                    subscription = Subscription.objects.create(
                        user=payment.user,
                        plan=payment.subscription_plan,
                        status='active',
                        current_period_start=timezone.now(),
                        current_period_end=timezone.now() + timezone.timedelta(
                            days=365 if payment.subscription_plan.billing_period == 'annual' else 30
                        ),
                        paymob_order_id=payment.paymob_order_id
                    )
                    SubscriptionUsage.objects.create(subscription=subscription)

                    # Ensure the user has a wallet (create one if missing)
                    Wallet.objects.get_or_create(user=payment.user)

                    # Notify user
                    send_notification_if_enabled(
                        recipient=payment.user,
                        notification_type='subscription',
                        title_ar='تم ترقية الخطة بنجاح',
                        title_en='Subscription Upgraded',
                        message_ar=f'تم تفعيل خطة "{payment.subscription_plan.name_ar}" بنجاح.',
                        message_en=f'Your "{payment.subscription_plan.name_en}" plan is now active.',
                        related_object=subscription
                    )
                
                # Notify customer
                if payment.payment_type == 'booking' and payment.booking:
                    msg_ar = f'تم تأكيد الدفع لخدمة "{payment.booking.service.title_ar}" بنجاح .'
                    msg_en = f'Payment for "{payment.booking.service.title_en}" was successful.'
                else:
                    msg_ar = f'تم تأكيد الدفع لخطة "{payment.subscription_plan.name_ar}" بنجاح.'
                    msg_en = f'Payment for "{payment.subscription_plan.name_en}" was successful.'

                send_notification_if_enabled(
                    recipient=payment.user,
                    notification_type='payment',
                    title_ar='تم الدفع بنجاح',
                    title_en='Payment Successful',
                    message_ar=msg_ar,
                    message_en=msg_en,
                    related_object=payment
                )
            else:
                payment.status = 'failed'
                payment.save()
                
                # Notify customer
                if payment.payment_type == 'booking' and payment.booking:
                    msg_ar = f'فشلت عملية الدفع لخدمة "{payment.booking.service.title_ar}". يرجى المحاولة مرة أخرى.'
                    msg_en = f'Payment for "{payment.booking.service.title_en}" failed. Please try again.'
                else:
                    msg_ar = f'فشلت عملية الدفع لخطة "{payment.subscription_plan.name_ar}". يرجى المحاولة مرة أخرى.'
                    msg_en = f'Payment for "{payment.subscription_plan.name_en}" failed. Please try again.'

                send_notification_if_enabled(
                    recipient=payment.user,
                    notification_type='payment',
                    title_ar='فشل الدفع',
                    title_en='Payment Failed',
                    message_ar=msg_ar,
                    message_en=msg_en,
                    related_object=payment
                )

            return Response(status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            logger.error(f"Received webhook for unknown Paymob Order ID: {order_id}")
            return Response(status=status.HTTP_404_NOT_FOUND)