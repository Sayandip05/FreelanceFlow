from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from .models import Project, ProjectSkill


def get_project_by_id(project_id: int) -> Project:
    """Get project by ID."""
    return get_object_or_404(Project, id=project_id)


def get_open_projects(
    budget_min: float | None = None,
    budget_max: float | None = None,
    skills: list[str] | None = None,
    search: str | None = None,
) -> QuerySet[Project]:
    """
    Get open projects with optional filtering.
    
    Args:
        budget_min: Minimum budget filter
        budget_max: Maximum budget filter
        skills: List of required skills
        search: Search term for title/description
    
    Returns:
        QuerySet of Project
    """
    queryset = Project.objects.filter(
        status=Project.Status.OPEN
    ).select_related('client').prefetch_related('skills')
    
    if budget_min is not None:
        queryset = queryset.filter(budget__gte=budget_min)
    
    if budget_max is not None:
        queryset = queryset.filter(budget__lte=budget_max)
    
    if skills:
        queryset = queryset.filter(skills__skill_name__in=skills).distinct()
    
    if search:
        queryset = queryset.filter(
            models.Q(title__icontains=search) |
            models.Q(description__icontains=search)
        )
    
    return queryset


def get_client_projects(client) -> QuerySet[Project]:
    """Get all projects for a specific client."""
    return Project.objects.filter(
        client=client
    ).select_related('client').prefetch_related('skills')


def get_project_skills(project: Project) -> list[str]:
    """Get list of skill names for a project."""
    return list(project.skills.values_list('skill_name', flat=True))
