from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from apps.projects.models import Project, ProjectSkill
from apps.users.models import User, FreelancerProfile


@registry.register_document
class ProjectDocument(Document):
    """Elasticsearch document for Project model."""
    
    client_name = fields.TextField(attr="client.get_full_name")
    client_email = fields.KeywordField(attr="client.email")
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
            "title",
            "description",
            "budget",
            "deadline",
            "created_at",
            "updated_at",
        ]
        related_models = [User]

        def get_queryset(self):
            return super().get_queryset().select_related('client').prefetch_related('skills')
    
    def prepare_skills(self, instance):
        """Prepare skills from related ProjectSkill model."""
        return [skill.skill_name for skill in instance.skills.all()]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.projects.all()
        return None


@registry.register_document
class FreelancerDocument(Document):
    """Elasticsearch document for Freelancer profiles."""
    
    email = fields.KeywordField(attr="user.email")
    full_name = fields.TextField(attr="user.get_full_name")
    skills = fields.KeywordField(multi=True, normalizer="lowercase_normalizer")
    
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
            "bio",
            "hourly_rate",
            "subscription_tier",
            "total_earned",
            "created_at",
        ]
        related_models = [User]

        def get_queryset(self):
            return super().get_queryset().select_related('user')
    
    def prepare_skills(self, instance):
        """Prepare skills from JSON field."""
        return instance.skills if instance.skills else []

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            if hasattr(related_instance, 'freelancer_profile'):
                return related_instance.freelancer_profile
        return None
