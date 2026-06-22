"""
Project Draft Services
"""
from django.db import transaction
from .models_extended import ProjectDraft


@transaction.atomic
def save_draft(client, title=None, description=None, budget=None, deadline=None, draft_data=None):
    """Save project as draft"""
    return ProjectDraft.objects.create(
        client=client,
        title=title,
        description=description,
        budget=budget,
        deadline=deadline,
        draft_data=draft_data or {}
    )


@transaction.atomic
def update_draft(draft_id, **kwargs):
    """Update draft"""
    draft = ProjectDraft.objects.get(id=draft_id)
    for key, value in kwargs.items():
        setattr(draft, key, value)
    draft.save()
    return draft


def get_user_drafts(client):
    """Get user's project drafts"""
    return ProjectDraft.objects.filter(client=client).order_by('-updated_at')


@transaction.atomic
def publish_draft(draft_id):
    """Convert draft to published project"""
    from .models import Project
    draft = ProjectDraft.objects.get(id=draft_id)
    
    project = Project.objects.create(
        client=draft.client,
        title=draft.title,
        description=draft.description,
        budget=draft.budget,
        deadline=draft.deadline
    )
    
    draft.delete()
    return project
