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
    id = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    full_name = serializers.CharField(required=False, allow_blank=True, default="")
    email = serializers.CharField(required=False, allow_blank=True, default="")
    avatar = serializers.CharField(required=False, allow_blank=True, default="")
    banner_image = serializers.CharField(required=False, allow_blank=True, default="")
    bio = serializers.CharField(required=False, allow_blank=True, default="")
    city = serializers.CharField(required=False, allow_blank=True, default="")
    country = serializers.CharField(required=False, allow_blank=True, default="")
    experience_level = serializers.CharField(required=False, allow_blank=True, default="")
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, default=0)
    average_rating = serializers.FloatField(required=False, allow_null=True, default=0)
    total_reviews = serializers.IntegerField(required=False, default=0)
    skills = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    subscription_tier = serializers.CharField(required=False, allow_blank=True, default="FREE")
    total_earned = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True, default=0)
    is_onboarded = serializers.BooleanField(required=False, default=True)
    freelancer_profile = serializers.SerializerMethodField()

    def get_id(self, obj):
        if isinstance(obj, dict):
            return obj.get("user_id") or obj.get("id")
        return getattr(obj, "user_id", getattr(obj, "id", None))

    def get_user_id(self, obj):
        return self.get_id(obj)

    def get_freelancer_profile(self, obj):
        if isinstance(obj, dict):
            existing_fp = obj.get("freelancer_profile")
            if existing_fp and isinstance(existing_fp, dict):
                return existing_fp
            return {
                "bio": obj.get("bio", ""),
                "skills": obj.get("skills", []),
                "hourly_rate": str(obj.get("hourly_rate") or "0.00"),
                "city": obj.get("city", ""),
                "country": obj.get("country", ""),
                "avatar": obj.get("avatar", ""),
                "banner_image": obj.get("banner_image", ""),
                "experience_level": obj.get("experience_level", ""),
                "average_rating": obj.get("average_rating", 0),
                "total_reviews": obj.get("total_reviews", 0),
                "is_onboarded": obj.get("is_onboarded", True),
            }
        return {
            "bio": getattr(obj, "bio", ""),
            "skills": getattr(obj, "skills", []),
            "hourly_rate": str(getattr(obj, "hourly_rate", "0.00")),
            "city": getattr(obj, "city", ""),
            "country": getattr(obj, "country", ""),
            "avatar": getattr(obj, "avatar", ""),
            "banner_image": getattr(obj, "banner_image", ""),
            "experience_level": getattr(obj, "experience_level", ""),
            "average_rating": getattr(obj, "average_rating", 0),
            "total_reviews": getattr(obj, "total_reviews", 0),
            "is_onboarded": getattr(obj, "is_onboarded", True),
        }


class SearchQuerySerializer(serializers.Serializer):
    """Serializer for search query parameters."""
    q = serializers.CharField(required=False, allow_blank=True, default="", help_text="Search query string")
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
