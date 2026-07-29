from django.contrib import admin
from apps.worklogs.models import WorkLog, WeeklyReport, DeliveryProof, ReportSchedule


@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    """Admin configuration for WorkLog model."""
    
    list_display = [
        "id",
        "contract",
        "date",
        "hours_worked",
        "created_at"
    ]
    list_filter = ["date", "created_at"]
    search_fields = [
        "contract__bid__project__title",
        "contract__bid__freelancer__email",
        "description"
    ]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "date"
    
    fieldsets = (
        ("Log Details", {
            "fields": ("contract", "freelancer", "date", "hours_worked", "description")
        }),
        ("Proof", {
            "fields": ("screenshot_url", "reference_url")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(WeeklyReport)
class WeeklyReportAdmin(admin.ModelAdmin):
    """Admin configuration for WeeklyReport model."""
    
    list_display = [
        "id",
        "contract",
        "week_start",
        "week_end",
        "sent_to_client_at",
        "created_at"
    ]
    list_filter = ["week_start", "sent_to_client_at"]
    search_fields = [
        "contract__bid__project__title",
        "ai_summary"
    ]
    readonly_fields = ["created_at"]
    date_hierarchy = "week_start"
    
    fieldsets = (
        ("Report Details", {
            "fields": ("contract", "week_start", "week_end", "ai_summary")
        }),
        ("Delivery", {
            "fields": ("pdf_url", "sent_to_client_at")
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )


@admin.register(DeliveryProof)
class DeliveryProofAdmin(admin.ModelAdmin):
    """Admin configuration for DeliveryProof model."""
    
    list_display = [
        "id",
        "contract",
        "report_id",
        "total_hours",
        "total_logs_count",
        "generated_at"
    ]
    search_fields = ["contract__bid__project__title", "report_id"]
    readonly_fields = ["generated_at"]
    date_hierarchy = "generated_at"


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    """Admin configuration for ReportSchedule model."""

    list_display = [
        "id",
        "contract",
        "interval_days",
        "next_report_date",
        "is_active",
        "created_at",
    ]
    list_filter = ["interval_days", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["contract__bid__project__title"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "next_report_date"

    fieldsets = (
        ("Schedule Settings", {
            "fields": ("contract", "interval_days", "next_report_date", "is_active", "created_by")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
