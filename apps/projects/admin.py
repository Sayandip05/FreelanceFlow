from django.contrib import admin
from apps.projects.models import Project, ProjectSkill


class ProjectSkillInline(admin.TabularInline):
    """Inline admin for project skills."""
    model = ProjectSkill
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin configuration for Project model."""
    
    list_display = [
        "title",
        "client",
        "status",
        "budget",
        "deadline",
        "created_at",
        "updated_at"
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "description", "client__email"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    inlines = [ProjectSkillInline]
    
    fieldsets = (
        ("Project Details", {
            "fields": ("title", "description", "client")
        }),
        ("Budget & Timeline", {
            "fields": ("budget", "deadline")
        }),
        ("Status", {
            "fields": ("status",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
