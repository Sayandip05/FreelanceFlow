from rest_framework import serializers


class ProjectSearchSerializer(serializers.Serializer):
    """Serializer for project search results."""
    id = serializers.IntegerField(required=False)
    title = serializers.CharField(required=False, allow_blank=True, default="")
    description = serializers.CharField(required=False, allow_blank=True, default="")
    budget = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, default=0)
    deadline = serializers.DateTimeField(required=False, allow_null=True)

    client_name = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    client_email = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    skills = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    status = serializers.CharField(required=False, allow_blank=True, default="OPEN")
    created_at = serializers.DateTimeField(required=False, allow_null=True)


class FreelancerSearchSerializer(serializers.Serializer):
    """Serializer for freelancer search results."""
    id = serializers.IntegerField(required=False)
    full_name = serializers.CharField(required=False, allow_blank=True, default="")
    email = serializers.CharField(required=False, allow_blank=True, default="")
    bio = serializers.CharField(required=False, allow_blank=True, default="")
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, default=0)
    skills = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    subscription_tier = serializers.CharField(required=False, allow_blank=True, default="FREE")
    total_earned = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True, default=0)


class SearchQuerySerializer(serializers.Serializer):
    """Serializer for search query parameters."""
    q = serializers.CharField(required=True, help_text="Search query string")
    type = serializers.ChoiceField(
        choices=["projects", "freelancers", "all"],
        default="all",
        help_text="Type of search"
    )
    skills = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Comma-separated list of skills to filter by"
    )
    min_budget = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Minimum budget filter for projects"
    )
    max_budget = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Maximum budget filter for projects"
    )
