from rest_framework import serializers


class ProjectSearchSerializer(serializers.Serializer):
    """Serializer for project search results."""
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    budget = serializers.DecimalField(max_digits=12, decimal_places=2)
    deadline = serializers.DateField(required=False, allow_null=True)
    client_name = serializers.CharField()
    client_email = serializers.CharField()
    skills = serializers.ListField(child=serializers.CharField())
    status = serializers.CharField()
    created_at = serializers.DateTimeField()


class FreelancerSearchSerializer(serializers.Serializer):
    """Serializer for freelancer search results."""
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    email = serializers.CharField()
    bio = serializers.CharField()
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    skills = serializers.ListField(child=serializers.CharField())
    subscription_tier = serializers.CharField()
    total_earned = serializers.DecimalField(max_digits=15, decimal_places=2)


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
