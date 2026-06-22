from django.contrib import admin
from apps.bidding.models import (
    Bid, Contract, Review, ReviewResponse, ContractTerminationRequest
)


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    """Admin configuration for Bid model."""

    list_display = ["id", "project", "freelancer", "amount", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["project__title", "freelancer__email", "proposal"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Bid Details", {"fields": ("project", "freelancer", "amount", "proposal")}),
        ("Status", {"fields": ("status",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """Admin configuration for Contract model."""

    list_display = ["id", "bid", "agreed_amount", "is_active", "start_date", "end_date"]
    list_filter = ["is_active", "start_date"]
    search_fields = ["bid__project__title", "bid__freelancer__email"]
    readonly_fields = ["start_date"]
    date_hierarchy = "start_date"

    fieldsets = (
        ("Contract Details", {"fields": ("bid", "agreed_amount", "is_active")}),
        ("Timeline", {"fields": ("start_date", "end_date")}),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin configuration for Review model."""

    list_display = [
        "id",
        "contract",
        "reviewer",
        "reviewee",
        "rating",
        "reviewer_type",
        "created_at",
    ]
    list_filter = ["rating", "reviewer_type", "created_at"]
    search_fields = ["reviewer__email", "reviewee__email", "review_text"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"


@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    """Admin configuration for ReviewResponse model."""

    list_display = ["id", "review", "created_at"]
    search_fields = ["review__id", "responder__email", "response_text"]
    readonly_fields = ["created_at"]


@admin.register(ContractTerminationRequest)
class ContractTerminationRequestAdmin(admin.ModelAdmin):
    """Admin configuration for ContractTerminationRequest model."""

    list_display = ["id", "contract", "requester", "reason", "status", "created_at"]
    list_filter = ["status", "reason", "created_at"]
    search_fields = ["contract__bid__project__title", "requested_by__email"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Termination Details",
            {"fields": ("contract", "requested_by", "reason", "status")},
        ),
        (
            "Refund Info",
            {"fields": ("refund_requested", "refund_amount"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
