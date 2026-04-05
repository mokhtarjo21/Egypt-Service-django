from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    SubscriptionPlan,
    Subscription,
    Invoice,
    AddonCredit,
    FeatureFlag,
    UsageRecord,
    Coupon,
    SubscriptionUsage,
    BillingAddress,
)


# -------------------------
# Subscription Plans
# -------------------------
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name_en",
        "plan_type",
        "billing_period",
        "price",
        "currency",
        "max_services",
        "max_team_members",
        "is_popular",
        "sort_order",
    )

    list_filter = (
        "plan_type",
        "billing_period",
        "is_popular",
        "has_advanced_analytics",
        "has_priority_support",
    )

    search_fields = ("name_ar", "name_en")
    ordering = ("sort_order", "price")

    fieldsets = (
        (_("Basic Info"), {
            "fields": (
                "name_ar",
                "name_en",
                "plan_type",
                "billing_period",
            )
        }),

        (_("Pricing"), {
            "fields": (
                "price",
                "currency",
                "stripe_price_id",
            )
        }),

        (_("Limits & Features"), {
            "fields": (
                "max_services",
                "max_team_members",
                "has_advanced_analytics",
                "has_priority_support",
                "search_ranking_boost",
                "featured_credits_included",
            )
        }),

        (_("Display"), {
            "fields": (
                "description_ar",
                "description_en",
                "features_ar",
                "features_en",
                "is_popular",
                "sort_order",
            )
        }),
    )


# -------------------------
# Addon Credits Inline
# -------------------------
class AddonCreditInline(admin.TabularInline):
    model = AddonCredit
    extra = 0
    readonly_fields = ("remaining_credits", "is_expired")


# -------------------------
# Subscription Usage Inline
# -------------------------
class SubscriptionUsageInline(admin.StackedInline):
    model = SubscriptionUsage
    extra = 0
    can_delete = False


# -------------------------
# Subscriptions
# -------------------------
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "status",
        "current_period_end",
        "services_count",
        "team_members_count",
        "is_active",
    )

    list_filter = (
        "status",
        "plan__plan_type",
        "plan__billing_period",
        "current_period_end",
    )

    search_fields = (
        "user__email",
        "user__full_name",
        "stripe_subscription_id",
    )

    readonly_fields = (
        "is_active",
        "days_until_renewal",
    )

    autocomplete_fields = ("user", "plan")

    inlines = [
        AddonCreditInline,
        SubscriptionUsageInline,
    ]

    fieldsets = (
        (_("Subscription"), {
            "fields": (
                "user",
                "plan",
                "status",
            )
        }),

        (_("Billing Period"), {
            "fields": (
                "current_period_start",
                "current_period_end",
                "trial_start",
                "trial_end",
                "canceled_at",
            )
        }),

        (_("Stripe"), {
            "fields": (
                "stripe_subscription_id",
                "stripe_customer_id",
            )
        }),

        (_("Paymob"), {
            "fields": ("paymob_order_id",)
        }),

        (_("Usage"), {
            "fields": (
                "services_count",
                "team_members_count",
                "featured_credits_used",
            )
        }),

        (_("Computed"), {
            "fields": (
                "is_active",
                "days_until_renewal",
            )
        }),
    )


# -------------------------
# Invoices
# -------------------------
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "subscription",
        "status",
        "total_amount",
        "currency",
        "due_date",
        "paid_at",
    )

    list_filter = (
        "status",
        "currency",
        "due_date",
        "created_at",
    )

    search_fields = (
        "invoice_number",
        "subscription__user__email",
        "stripe_invoice_id",
    )

    readonly_fields = (
        "invoice_number",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = ("subscription",)


# -------------------------
# Addon Credits
# -------------------------
@admin.register(AddonCredit)
class AddonCreditAdmin(admin.ModelAdmin):
    list_display = (
        "subscription",
        "credit_type",
        "amount",
        "used_amount",
        "remaining_credits",
        "expires_at",
        "is_expired",
    )

    list_filter = (
        "credit_type",
        "expires_at",
    )

    search_fields = (
        "subscription__user__email",
    )

    autocomplete_fields = ("subscription",)


# -------------------------
# Feature Flags
# -------------------------
@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "name_en",
        "is_global",
    )

    search_fields = (
        "key",
        "name_en",
        "name_ar",
    )

    list_filter = ("is_global",)


# -------------------------
# Usage Records
# -------------------------
@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = (
        "subscription",
        "usage_type",
        "quantity",
        "total_amount",
        "timestamp",
    )

    list_filter = (
        "usage_type",
        "timestamp",
    )

    search_fields = (
        "subscription__user__email",
    )

    autocomplete_fields = ("subscription",)

    readonly_fields = (
        "timestamp",
    )


# -------------------------
# Coupons
# -------------------------
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name_en",
        "discount_type",
        "discount_value",
        "valid_from",
        "valid_until",
        "used_count",
        "is_valid",
    )

    list_filter = (
        "discount_type",
        "valid_from",
        "valid_until",
        "first_time_only",
    )

    search_fields = (
        "code",
        "name_en",
        "name_ar",
    )

    filter_horizontal = ("applicable_plans",)

    readonly_fields = (
        "used_count",
        "is_valid",
    )


# -------------------------
# Subscription Usage
# -------------------------
@admin.register(SubscriptionUsage)
class SubscriptionUsageAdmin(admin.ModelAdmin):
    list_display = (
        "subscription",
        "services_count",
        "team_members_count",
        "storage_used_mb",
        "monthly_api_calls",
        "monthly_messages_sent",
        "last_reset_at",
    )

    search_fields = (
        "subscription__user__email",
    )

    autocomplete_fields = ("subscription",)


# -------------------------
# Billing Address
# -------------------------
@admin.register(BillingAddress)
class BillingAddressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company_name",
        "city",
        "governorate",
        "country",
        "is_default",
    )

    list_filter = (
        "country",
        "governorate",
        "is_default",
    )

    search_fields = (
        "user__email",
        "company_name",
        "city",
    )

    autocomplete_fields = ("user",)