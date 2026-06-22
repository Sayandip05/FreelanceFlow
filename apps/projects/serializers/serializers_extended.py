"""
Serializers for Extended Project Features
"""
from rest_framework import serializers
from .models_extended import ProjectBookmark


class ProjectBookmarkSerializer(serializers.ModelSerializer):
    """Serializer for project bookmarks"""
    project_id = serializers.IntegerField(source='project.id', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    project_budget = serializers.DecimalField(
        source='project.budget',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    project_status = serializers.CharField(source='project.status', read_only=True)
    client_email = serializers.EmailField(source='project.client.email', read_only=True)
    
    class Meta:
        model = ProjectBookmark
        fields = [
            'id', 'project_id', 'project_title', 'project_budget',
            'project_status', 'client_email', 'created_at'
        ]
        read_only_fields = fields


class BookmarkProjectSerializer(serializers.Serializer):
    """Serializer for bookmarking a project"""
    project_id = serializers.IntegerField()
