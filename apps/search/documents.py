from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from apps.projects.models import Project, ProjectSkill
from apps.users.models import User, FreelancerProfile


@registry.register_document
class ProjectDocument(Document):
    """Elasticsearch document for Project model with lightweight indexing."""
    
    title = fields.TextField()
    description = fields.TextField()
    client_name = fields.TextField(attr="client.get_full_name")
    client_email = fields.KeywordField(attr="client.email", index=False)
    skills = fields.KeywordField(multi=True, normalizer="lowercase_normalizer")
    status = fields.KeywordField()
    
    class Index:
        name = "projects"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "normalizer": {
                    "lowercase_normalizer": {
                        "type": "custom",
                        "char_filter": [],
                        "filter": ["lowercase"]
                    }
                }
            }
        }
    
    class Django:
        model = Project
        fields = [
            "id",
            "budget",
            "deadline",
            "approx_duration",
            "created_at",
        ]
        related_models = [User]

        def get_queryset(self):
            return super().get_queryset().select_related('client').prefetch_related('skills')
    
    def prepare_description(self, instance):
        """Index only first 400 characters of description to save index size."""
        if not instance.description:
            return ""
        return instance.description[:400]

    def prepare_skills(self, instance):
        """Prepare skills from related ProjectSkill model."""
        return [skill.skill_name for skill in instance.skills.all()]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.projects.all()
        return None


@registry.register_document
class FreelancerDocument(Document):
    """Elasticsearch document for Freelancer profiles with lightweight indexing."""
    
    user_id = fields.IntegerField(attr="user_id")
    email = fields.KeywordField(attr="user.email")
    first_name = fields.TextField(attr="user.first_name")
    last_name = fields.TextField(attr="user.last_name")
    full_name = fields.TextField(attr="user.get_full_name")
    bio = fields.TextField()
    skills = fields.KeywordField(multi=True, normalizer="lowercase_normalizer")
    avatar = fields.KeywordField(attr="avatar", index=False)
    banner_image = fields.KeywordField(attr="banner_image", index=False)
    city = fields.KeywordField(attr="city")
    country = fields.KeywordField(attr="country")
    experience_level = fields.KeywordField(attr="experience_level")
    average_rating = fields.FloatField(attr="average_rating")
    total_reviews = fields.IntegerField(attr="total_reviews")
    is_onboarded = fields.BooleanField(attr="is_onboarded")
    
    class Index:
        name = "freelancers"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "normalizer": {
                    "lowercase_normalizer": {
                        "type": "custom",
                        "char_filter": [],
                        "filter": ["lowercase"]
                    }
                }
            }
        }
    
    class Django:
        model = FreelancerProfile
        fields = [
            "id",
            "hourly_rate",
            "total_earned",
            "created_at",
        ]
        related_models = [User]

        def get_queryset(self):
            return super().get_queryset().select_related('user')
    
    def prepare_bio(self, instance):
        """Index only first 300 characters of bio to keep index lightweight."""
        if not instance.bio:
            return ""
        return instance.bio[:300]

    def prepare_skills(self, instance):
        """Prepare skills from JSON field."""
        return instance.skills if instance.skills else []

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            if hasattr(related_instance, 'freelancer_profile'):
                return related_instance.freelancer_profile
        return None
