from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet, 
    WalletViewSet, 
    PaymobCheckoutView, 
    PaymobWebhookView,
    PaymentViewSet,
    WalletViewSet,
    PaymobCheckoutView,
    PaymobWebhookView,
    PaymobSubscriptionCheckoutView
)

app_name = 'payments'

router = DefaultRouter()
router.register('history', PaymentViewSet, basename='payment')
router.register(r'wallet', WalletViewSet, basename='wallet')

urlpatterns = [
    path('checkout/paymob/', PaymobCheckoutView.as_view(), name='paymob-checkout'),
    path('checkout/subscription/paymob/', PaymobSubscriptionCheckoutView.as_view(), name='paymob-subscription-checkout'),
    path('webhook/paymob/', PaymobWebhookView.as_view(), name='paymob-webhook'),
    path('', include(router.urls)),
]