"""
Project Bookmark Services
"""
from django.db import transaction
from .models_extended import ProjectBookmark


@transaction.atomic
def bookmark_project(user, project):
    """Bookmark a project"""
    bookmark, created = ProjectBookmark.objects.get_or_create(
        user=user,
        project=project
    )
    return bookmark


@transaction.atomic
def remove_bookmark(user, project):
    """Remove project bookmark"""
    ProjectBookmark.objects.filter(user=user, project=project).delete()


def get_bookmarked_projects(user):
    """Get user's bookmarked projects"""
    return ProjectBookmark.objects.filter(user=user).select_related('project')


def is_bookmarked(user, project):
    """Check if project is bookmarked"""
    return ProjectBookmark.objects.filter(user=user, project=project).exists()
