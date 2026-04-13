from rest_framework import serializers

from .models import Project, ProjectSkill
from apps.users.serializers import UserSerializer
from core.sanitizers import sanitize_html


class ProjectSkillSerializer(serializers.ModelSerializer):
    """Serializer for project skills."""
    
    class Meta:
        model = ProjectSkill
        fields = ['id', 'skill_name']


class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer for project list view."""
    client = UserSerializer(read_only=True)
    skills = ProjectSkillSerializer(many=True, read_only=True)
    skill_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Project
        fields = [
            'id',
            'client',
            'title',
            'description',
            'budget',
            'deadline',
            'status',
            'skills',
            'skill_names',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Serializer for project detail view."""
    client = UserSerializer(read_only=True)
    skills = ProjectSkillSerializer(many=True, read_only=True)
    skill_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Project
        fields = [
            'id',
            'client',
            'title',
            'description',
            'budget',
            'deadline',
            'status',
            'skills',
            'skill_names',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating projects."""
    skill_names = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    
    class Meta:
        model = Project
        fields = [
            'title',
            'description',
            'budget',
            'deadline',
            'skill_names',
        ]
    
    def validate_budget(self, value):
        if value <= 0:
            raise serializers.ValidationError("Budget must be greater than 0.")
        return value
    
    def validate_title(self, value):
        """Sanitize title to prevent XSS."""
        return sanitize_html(value, allow_basic_formatting=False)
    
    def validate_description(self, value):
        """Sanitize description to prevent XSS."""
        return sanitize_html(value, allow_basic_formatting=True)


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating projects."""
    skill_names = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    
    class Meta:
        model = Project
        fields = [
            'title',
            'description',
            'budget',
            'deadline',
            'skill_names',
        ]
    
    def validate_budget(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Budget must be greater than 0.")
        return value
    
    def validate_title(self, value):
        """Sanitize title to prevent XSS."""
        if value:
            return sanitize_html(value, allow_basic_formatting=False)
        return value
    
    def validate_description(self, value):
        """Sanitize description to prevent XSS."""
        if value:
            return sanitize_html(value, allow_basic_formatting=True)
        return value
