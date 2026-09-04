from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.users.models import User, FreelancerProfile, ClientProfile
class FreelancerProfileInline(admin.StackedInline):
    """Inline admin for FreelancerProfile."""
    model = FreelancerProfile
    can_delete = False
    verbose_name_plural = "Freelancer Profile"


class ClientProfileInline(admin.StackedInline):
    """Inline admin for ClientProfile."""
    model = ClientProfile
    can_delete = False
    verbose_name_plural = "Client Profile"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin with role-based fields."""
    
    list_display = [
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "date_joined"
    ]
    list_filter = ["role", "is_staff", "is_superuser", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]
    
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Role", {"fields": ("role",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role"),
        }),
    )
    
    def get_inlines(self, request, obj=None):
        """Return appropriate inline based on user role."""
        if obj is None:
            return []
        if obj.role == User.Roles.FREELANCER:
            return [FreelancerProfileInline]
        elif obj.role == User.Roles.CLIENT:
            return [ClientProfileInline]
        return []
