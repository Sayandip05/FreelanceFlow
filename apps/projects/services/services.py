import logging
from django.db import transaction
from django.db.models import QuerySet
from apps.projects.models import Project, ProjectSkill
from core.exceptions import ValidationError, PermissionDeniedError
logger = logging.getLogger("apps.projects")


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
    from apps.users.models import User
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

        if skills:
            ProjectSkill.objects.bulk_create([
                ProjectSkill(project=project, skill_name=skill.strip())
                for skill in skills
                if skill.strip()
            ])

    logger.info(
        "Project created: project_id=%s client_id=%s title=%r budget=%s",
        project.id, client.id, title, budget,
    )
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

        if skills is not None:
            project.skills.all().delete()
            ProjectSkill.objects.bulk_create([
                ProjectSkill(project=project, skill_name=skill.strip())
                for skill in skills
                if skill.strip()
            ])

    logger.info(
        "Project updated: project_id=%s updated_by=%s",
        project.id, user.id,
    )
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

    logger.info(
        "Project cancelled: project_id=%s closed_by=%s",
        project.id, user.id,
    )
    return project


def delete_project(project: Project, user) -> bool:
    """
    Permanently delete a project. Only the client owner can delete it.
    Projects with in-progress or completed contracts cannot be deleted.
    """
    if project.client != user:
        raise PermissionDeniedError("Only the project owner can delete it.")
    
    from apps.bidding.models import Contract
    has_active_contracts = Contract.objects.filter(
        bid__project=project,
        status__in=[Contract.Status.ACTIVE, Contract.Status.COMPLETED, Contract.Status.DISPUTED]
    ).exists()
    
    if has_active_contracts or project.status in [Project.Status.IN_PROGRESS, Project.Status.COMPLETED]:
        raise ValidationError("Cannot delete a project that is in progress or has active contracts.")
        
    project_id = project.id
    project.delete()

    logger.info("Project deleted: project_id=%s deleted_by=%s", project_id, user.id)
    return True


def mark_project_in_progress(project: Project) -> Project:
    """
    Mark project as in progress (called when bid is accepted).
    """
    if project.status != Project.Status.OPEN:
        raise ValidationError("Project must be open to start progress.")
    
    project.status = Project.Status.IN_PROGRESS
    project.save()

    logger.info("Project moved to IN_PROGRESS: project_id=%s", project.id)
    return project


def mark_project_completed(project: Project) -> Project:
    """
    Mark project as completed (called when payment is released).
    """
    if project.status != Project.Status.IN_PROGRESS:
        raise ValidationError("Project must be in progress to complete.")
    
    project.status = Project.Status.COMPLETED
    project.save()

    logger.info("Project completed: project_id=%s", project.id)
    return project
