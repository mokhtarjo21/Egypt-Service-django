"""
Views for the subscriptions app.
"""

from decimal import Decimal
from django.utils import timezone
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import stripe
from django.conf import settings

from .models import (
    SubscriptionPlan, 
    Subscription, 
    Invoice, 
    AddonCredit, 
    Coupon, 
    SubscriptionUsage,
    BillingAddress
)
from .serializers import (
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
    InvoiceSerializer,
    AddonCreditSerializer,
    CouponSerializer,
    SubscriptionUsageSerializer,
    BillingAddressSerializer,
    SubscriptionCreateSerializer,
    CouponValidationSerializer
)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for subscription plans.
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return self.queryset.order_by('sort_order', 'price')


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user subscriptions.
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def create(self, request):
        """
        Create a new subscription with Stripe integration.
        """
        serializer = SubscriptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        plan_id = serializer.validated_data['plan_id']
        payment_method_id = serializer.validated_data['payment_method_id']
        coupon_code = serializer.validated_data.get('coupon_code')
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already has an active subscription
        existing_subscription = Subscription.objects.filter(
            user=request.user,
            status='active'
        ).first()
        
        if existing_subscription:
            return Response(
                {'error': 'User already has an active subscription'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create or retrieve Stripe customer
            stripe_customer = None
            if hasattr(request.user, 'stripe_customer_id') and request.user.stripe_customer_id:
                stripe_customer = stripe.Customer.retrieve(request.user.stripe_customer_id)
            else:
                stripe_customer = stripe.Customer.create(
                    email=request.user.email,
                    phone=str(request.user.phone_number),
                    name=request.user.full_name,
                    metadata={'user_id': str(request.user.id)}
                )
                request.user.stripe_customer_id = stripe_customer.id
                request.user.save()
            
            # Attach payment method
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=stripe_customer.id
            )
            
            # Apply coupon if provided
            coupon_discount = None
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                    if coupon.is_valid:
                        coupon_discount = coupon.calculate_discount(plan.price)
                except Coupon.DoesNotExist:
                    pass
            
            # Create Stripe subscription
            stripe_subscription = stripe.Subscription.create(
                customer=stripe_customer.id,
                items=[{'price': plan.stripe_price_id}],
                default_payment_method=payment_method_id,
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'user_id': str(request.user.id),
                    'plan_type': plan.plan_type
                }
            )
            
            # Create local subscription
            subscription = Subscription.objects.create(
                user=request.user,
                plan=plan,
                status='active',
                current_period_start=timezone.now(),
                current_period_end=timezone.now() + timezone.timedelta(
                    days=365 if plan.billing_period == 'annual' else 30
                ),
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=stripe_customer.id
            )
            
            # Create usage tracking
            SubscriptionUsage.objects.create(subscription=subscription)
            
            # Update coupon usage
            if coupon_code and coupon_discount:
                coupon.used_count += 1
                coupon.save()
            
            return Response({
                'subscription': SubscriptionSerializer(subscription).data,
                'client_secret': stripe_subscription.latest_invoice.payment_intent.client_secret
            })
            
        except stripe.error.StripeError as e:
            return Response(
                {'error': f'Payment failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a subscription.
        """
        subscription = self.get_object()
        
        try:
            # Cancel Stripe subscription
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            subscription.canceled_at = timezone.now()
            subscription.save()
            
            return Response({'message': 'Subscription canceled successfully'})
            
        except stripe.error.StripeError as e:
            return Response(
                {'error': f'Cancellation failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def upgrade(self, request, pk=None):
        """
        Upgrade subscription plan.
        """
        subscription = self.get_object()
        new_plan_id = request.data.get('plan_id')
        
        try:
            new_plan = SubscriptionPlan.objects.get(id=new_plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Update Stripe subscription with proration
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': subscription.stripe_subscription_id,
                    'price': new_plan.stripe_price_id,
                }],
                proration_behavior='create_prorations'
            )
            
            subscription.plan = new_plan
            subscription.save()
            
            return Response({
                'subscription': SubscriptionSerializer(subscription).data
            })
            
        except stripe.error.StripeError as e:
            return Response(
                {'error': f'Upgrade failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for invoices.
    """
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Invoice.objects.filter(subscription__user=self.request.user)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download invoice PDF.
        """
        invoice = self.get_object()
        if invoice.pdf_file:
            # Return signed URL for PDF download
            return Response({'download_url': invoice.pdf_file.url})
        else:
            # Generate PDF on demand
            # TODO: Implement PDF generation
            return Response({'error': 'PDF not available'}, status=status.HTTP_404_NOT_FOUND)


class AddonCreditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for addon credits.
    """
    serializer_class = AddonCreditSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AddonCredit.objects.filter(subscription__user=self.request.user)


class CouponValidationView(generics.GenericAPIView):
    """
    Validate coupon codes.
    """
    serializer_class = CouponValidationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        plan_id = serializer.validated_data['plan_id']
        
        try:
            coupon = Coupon.objects.get(code=code)
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            if not coupon.is_valid:
                return Response({'error': 'Coupon is not valid'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check plan applicability
            if coupon.applicable_plans.exists() and plan not in coupon.applicable_plans.all():
                return Response({'error': 'Coupon not applicable to this plan'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check minimum amount
            if coupon.minimum_amount and plan.price < coupon.minimum_amount:
                return Response({'error': 'Plan price below minimum amount'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check first-time only
            if coupon.first_time_only and Subscription.objects.filter(user=request.user).exists():
                return Response({'error': 'Coupon is for first-time customers only'}, status=status.HTTP_400_BAD_REQUEST)
            
            discount_amount = coupon.calculate_discount(plan.price)
            final_price = plan.price - discount_amount
            
            return Response({
                'valid': True,
                'discount_amount': discount_amount,
                'final_price': final_price,
                'coupon': CouponSerializer(coupon).data
            })
            
        except (Coupon.DoesNotExist, SubscriptionPlan.DoesNotExist):
            return Response({'error': 'Invalid coupon or plan'}, status=status.HTTP_400_BAD_REQUEST)
from rest_framework.response import Response

class SubscriptionUsageView(generics.RetrieveAPIView):
    serializer_class = SubscriptionUsageSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        subscription = Subscription.objects.filter(
            user=request.user,
            status='active'
        ).first()

        if not subscription:
            return Response({
                "is_free": True,
                "services_count": 0,
                "team_members_count": 1,
                "featured_credits_used": 0,
                "storage_used_mb": 0,
                "monthly_api_calls": 0,
                "monthly_messages_sent": 0,
            })

        usage, _ = SubscriptionUsage.objects.get_or_create(
            subscription=subscription
        )

        serializer = self.get_serializer(usage)
        return Response(serializer.data)


class BillingAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for billing addresses.
    """
    serializer_class = BillingAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BillingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Admin Views
class AdminSubscriptionView(generics.ListAPIView):
    """
    Admin view for all subscriptions.
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.role == 'admin':
            return Subscription.objects.none()
        return Subscription.objects.all().order_by('-created_at')


class AdminCouponViewSet(viewsets.ModelViewSet):
    """
    Admin viewset for coupons.
    """
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.role == 'admin':
            return Coupon.objects.none()
        return super().get_queryset()

class AdminSubscriptionPlanViewSet(viewsets.ModelViewSet):
    """
    Admin viewset for subscription plans.
    """
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not hasattr(user, 'role') or user.role != 'admin':
            return SubscriptionPlan.objects.none()
        return super().get_queryset().order_by('sort_order', 'price')


class AdminSubscriptionStatsView(generics.GenericAPIView):
    """
    Admin view for real-time subscription statistics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.role == 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        from django.db.models import Sum, Count, Q
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_subscriptions = Subscription.objects.count()
        active_subscriptions = Subscription.objects.filter(status='active').count()
        canceled_subscriptions = Subscription.objects.filter(status='canceled').count()

        # Monthly revenue: sum of active subscriptions that are monthly
        monthly_subs_revenue = Subscription.objects.filter(
            status='active',
            plan__billing_period='monthly'
        ).aggregate(total=Sum('plan__price'))['total'] or 0

        # Annual revenue: annualize monthly + annual plans
        annual_subs_revenue = Subscription.objects.filter(
            status='active',
            plan__billing_period='annual'
        ).aggregate(total=Sum('plan__price'))['total'] or 0

        monthly_revenue = float(monthly_subs_revenue)
        annual_revenue = float(monthly_subs_revenue * 12 + annual_subs_revenue)

        # Churn rate: canceled / total * 100
        churn_rate = round((canceled_subscriptions / total_subscriptions * 100), 1) if total_subscriptions else 0

        # Average revenue per user
        avg_revenue_per_user = round(monthly_revenue / active_subscriptions, 2) if active_subscriptions else 0

        # New subscriptions this month
        new_this_month = Subscription.objects.filter(created_at__gte=month_start).count()

        return Response({
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'canceled_subscriptions': canceled_subscriptions,
            'monthly_revenue': monthly_revenue,
            'annual_revenue': annual_revenue,
            'churn_rate': churn_rate,
            'avg_revenue_per_user': avg_revenue_per_user,
            'new_this_month': new_this_month,
        })