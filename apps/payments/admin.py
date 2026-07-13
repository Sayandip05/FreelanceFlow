from django.contrib import admin
from apps.payments.models import (
    Payment,
    Escrow,
    PlatformEarning,
    PaymentEvent,
    PaymentDispute,
    DisputeMessage,
)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment model."""

    list_display = [
        "id",
        "contract",
        "total_amount",
        "status",
        "razorpay_order_id",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["contract__bid__project__title", "razorpay_order_id"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Payment Details", {"fields": ("contract", "total_amount", "status")}),
        ("Razorpay", {"fields": ("razorpay_order_id", "razorpay_payment_id"), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    """Admin configuration for Escrow model."""

    list_display = ["id", "payment", "held_amount", "released_at"]
    search_fields = ["payment__contract__bid__project__title"]
    readonly_fields = ["released_at"]


@admin.register(PlatformEarning)
class PlatformEarningAdmin(admin.ModelAdmin):
    """Admin configuration for PlatformEarning model."""

    list_display = ["id", "payment", "cut_percentage", "cut_amount", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["payment__contract__bid__project__title"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentEvent model."""

    list_display = ["id", "payment", "event_type", "razorpay_event_id", "processed_at"]
    list_filter = ["event_type", "processed_at"]
    search_fields = ["razorpay_event_id", "event_type"]
    readonly_fields = ["processed_at"]
    date_hierarchy = "processed_at"


@admin.register(PaymentDispute)
class PaymentDisputeAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentDispute model."""

    list_display = ["id", "payment", "disputer", "reason", "status", "created_at"]
    list_filter = ["status", "reason", "created_at"]
    search_fields = ["payment__contract__bid__project__title", "disputer__email"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Dispute Details", {"fields": ("payment", "disputer", "reason", "status")}),
        (
            "Resolution",
            {
                "fields": ("resolution", "resolved_by", "resolved_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(DisputeMessage)
class DisputeMessageAdmin(admin.ModelAdmin):
    """Admin configuration for DisputeMessage model."""

    list_display = ["id", "dispute", "sender", "created_at"]
    search_fields = ["dispute__id", "sender__email", "message"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
