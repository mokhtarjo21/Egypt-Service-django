from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'plans', views.SubscriptionPlanViewSet, basename='plans')
router.register(r'subscriptions', views.SubscriptionViewSet, basename='subscriptions')
router.register(r'invoices', views.InvoiceViewSet, basename='invoices')
router.register(r'credits', views.AddonCreditViewSet, basename='credits')
router.register(r'billing-addresses', views.BillingAddressViewSet, basename='billing-addresses')

# Admin routes
router.register(r'admin/coupons', views.AdminCouponViewSet, basename='admin-coupons')
router.register(r'admin/plans', views.AdminSubscriptionPlanViewSet, basename='admin-plans')

app_name = 'subscriptions'

urlpatterns = [
    path('', include(router.urls)),
    path('validate-coupon/', views.CouponValidationView.as_view(), name='validate-coupon'),
    path('usage/', views.SubscriptionUsageView.as_view(), name='subscription-usage'),
    path('admin/subscriptions/', views.AdminSubscriptionView.as_view(), name='admin-subscriptions'),
    path('admin/stats/', views.AdminSubscriptionStatsView.as_view(), name='admin-stats'),
]