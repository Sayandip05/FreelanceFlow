from django.db import transaction
from django.db.models import QuerySet

from .models import Project, ProjectSkill
from core.exceptions import ValidationError, PermissionDeniedError


def create_project(
    client,
    title: str,
    description: str,
    budget: float,
    deadline: str | None = None,
    skills: list[str] | None = None,
) -> Project:
    """
    Create a new project.
    
    Args:
        client: User instance (must be a client)
        title: Project title
        description: Project description
        budget: Project budget
        deadline: Optional deadline date (ISO format)
        skills: Optional list of required skills
    
    Returns:
        Created Project instance
    """
    from users.models import User
    
    if client.role != User.Roles.CLIENT:
        raise PermissionDeniedError("Only clients can create projects.")
    
    if not title:
        raise ValidationError("Title is required.", field="title")
    
    if not description:
        raise ValidationError("Description is required.", field="description")
    
    if budget <= 0:
        raise ValidationError("Budget must be greater than 0.", field="budget")
    
    with transaction.atomic():
        project = Project.objects.create(
            client=client,
            title=title,
            description=description,
            budget=budget,
            deadline=deadline,
        )
        
        # Create skills
        if skills:
            ProjectSkill.objects.bulk_create([
                ProjectSkill(project=project, skill_name=skill.strip())
                for skill in skills
                if skill.strip()
            ])
        
        return project


def update_project(
    project: Project,
    user,
    title: str | None = None,
    description: str | None = None,
    budget: float | None = None,
    deadline: str | None = None,
    skills: list[str] | None = None,
) -> Project:
    """
    Update a project. Only the client who created it can update.
    Can only update if project is OPEN.
    """
    if project.client != user:
        raise PermissionDeniedError("Only the project owner can update it.")
    
    if project.status != Project.Status.OPEN:
        raise ValidationError(
            "Cannot update project that is not open.",
            field="status"
        )
    
    with transaction.atomic():
        if title is not None:
            project.title = title
        if description is not None:
            project.description = description
        if budget is not None:
            if budget <= 0:
                raise ValidationError("Budget must be greater than 0.", field="budget")
            project.budget = budget
        if deadline is not None:
            project.deadline = deadline
        
        project.save()
        
        # Update skills if provided
        if skills is not None:
            project.skills.all().delete()
            ProjectSkill.objects.bulk_create([
                ProjectSkill(project=project, skill_name=skill.strip())
                for skill in skills
                if skill.strip()
            ])
        
        return project


def close_project(project: Project, user) -> Project:
    """
    Close/cancel a project. Only the client who created it can close.
    """
    if project.client != user:
        raise PermissionDeniedError("Only the project owner can close it.")
    
    if project.status == Project.Status.COMPLETED:
        raise ValidationError("Cannot close a completed project.")
    
    project.status = Project.Status.CANCELLED
    project.save()
    
    return project


def mark_project_in_progress(project: Project) -> Project:
    """
    Mark project as in progress (called when bid is accepted).
    """
    if project.status != Project.Status.OPEN:
        raise ValidationError("Project must be open to start progress.")
    
    project.status = Project.Status.IN_PROGRESS
    project.save()
    
    return project


def mark_project_completed(project: Project) -> Project:
    """
    Mark project as completed (called when payment is released).
    """
    if project.status != Project.Status.IN_PROGRESS:
        raise ValidationError("Project must be in progress to complete.")
    
    project.status = Project.Status.COMPLETED
    project.save()
    
    return project
