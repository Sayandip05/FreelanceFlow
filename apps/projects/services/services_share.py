"""
Project Share Services
"""
from django.db import transaction
import secrets
from .models_extended import ProjectShare


@transaction.atomic
def generate_share_link(project, expires_at=None):
    """Generate public share link for project"""
    share_token = secrets.token_urlsafe(32)
    
    return ProjectShare.objects.create(
        project=project,
        share_token=share_token,
        expires_at=expires_at,
        is_active=True
    )


def get_project_by_token(token):
    """Get project by share token"""
    from django.utils import timezone
    
    share = ProjectShare.objects.select_related('project').get(
        share_token=token,
        is_active=True
    )
    
    # Check expiry
    if share.expires_at and share.expires_at < timezone.now():
        raise ValueError("Share link expired")
    
    # Increment view count
    share.view_count += 1
    share.save()
    
    return share.project


@transaction.atomic
def deactivate_share_link(share_id):
    """Deactivate share link"""
    share = ProjectShare.objects.get(id=share_id)
    share.is_active = False
    share.save()
