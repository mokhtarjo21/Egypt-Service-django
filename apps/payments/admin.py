from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Payment, Wallet, WalletTransaction


# -----------------------------
# Wallet Transactions Inline
# -----------------------------
class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    autocomplete_fields = ("payment",)
    readonly_fields = ("created_at",)


# -----------------------------
# Payments
# -----------------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "amount",
        "currency",
        "status",
        "payment_type",
        "payment_method",
        "transaction_id",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_type",
        "payment_method",
        "currency",
        "created_at",
    )

    search_fields = (
        "transaction_id",
        "paymob_order_id",
        "mobile_number",
        "user__email",
        "user__full_name",
    )

    autocomplete_fields = (
        "user",
        "booking",
        "subscription_plan",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (_("Payment Info"), {
            "fields": (
                "user",
                "amount",
                "currency",
                "status",
                "payment_type",
                "payment_method",
            )
        }),

        (_("Relations"), {
            "fields": (
                "booking",
                "subscription_plan",
            )
        }),

        (_("Gateway Info"), {
            "fields": (
                "transaction_id",
                "paymob_order_id",
                "mobile_number",
            )
        }),

        (_("Timestamps"), {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )


# -----------------------------
# Wallet
# -----------------------------
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "balance",
        "currency",
        "is_frozen",
        "created_at",
    )

    list_filter = (
        "currency",
        "is_frozen",
    )

    search_fields = (
        "user__email",
        "user__full_name",
    )

    autocomplete_fields = ("user",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [WalletTransactionInline]


# -----------------------------
# Wallet Transactions
# -----------------------------
@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "wallet",
        "transaction_type",
        "amount",
        "payment",
        "created_at",
    )

    list_filter = (
        "transaction_type",
        "created_at",
    )

    search_fields = (
        "wallet__user__email",
        "wallet__user__full_name",
        "description",
    )

    autocomplete_fields = (
        "wallet",
        "payment",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (_("Transaction Info"), {
            "fields": (
                "wallet",
                "transaction_type",
                "amount",
                "description",
            )
        }),

        (_("Related Objects"), {
            "fields": (
                "payment",
            )
        }),

        (_("Timestamps"), {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )