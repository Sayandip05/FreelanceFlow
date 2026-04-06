from django.contrib import admin
from apps.bidding.models import Bid, Contract


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    """Admin configuration for Bid model."""
    
    list_display = [
        "id",
        "project",
        "freelancer",
        "amount",
        "status",
        "created_at"
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["project__title", "freelancer__email", "proposal"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("Bid Details", {
            "fields": ("project", "freelancer", "amount", "proposal")
        }),
        ("Status", {
            "fields": ("status",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """Admin configuration for Contract model."""
    
    list_display = [
        "id",
        "bid",
        "agreed_amount",
        "is_active",
        "start_date",
        "end_date"
    ]
    list_filter = ["is_active", "start_date"]
    search_fields = ["bid__project__title", "bid__freelancer__email"]
    readonly_fields = ["start_date"]
    date_hierarchy = "start_date"
    
    fieldsets = (
        ("Contract Details", {
            "fields": ("bid", "agreed_amount", "is_active")
        }),
        ("Timeline", {
            "fields": ("start_date", "end_date")
        }),
    )
