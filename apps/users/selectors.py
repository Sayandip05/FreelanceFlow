from django.shortcuts import get_object_or_404
from .models import User, FreelancerProfile, ClientProfile


def get_user_by_id(user_id: int) -> User:
    """Get user by ID."""
    return get_object_or_404(User, id=user_id)


def get_user_by_email(email: str) -> User | None:
    """Get user by email."""
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None


def get_freelancer_profile(user: User) -> FreelancerProfile | None:
    """Get freelancer profile for a user."""
    try:
        return user.freelancer_profile
    except FreelancerProfile.DoesNotExist:
        return None


def get_client_profile(user: User) -> ClientProfile | None:
    """Get client profile for a user."""
    try:
        return user.client_profile
    except ClientProfile.DoesNotExist:
        return None


def list_freelancers(skills: list[str] | None = None, limit: int = 50):
    """
    List freelancers with optional skill filtering.
    
    Args:
        skills: Optional list of skills to filter by
        limit: Maximum number of results
    
    Returns:
        QuerySet of FreelancerProfile
    """
    queryset = FreelancerProfile.objects.select_related('user').all()
    
    if skills:
        # Filter freelancers who have any of the specified skills
        queryset = queryset.filter(skills__overlap=skills)
    
    return queryset[:limit]


def list_clients(limit: int = 50):
    """List clients."""
    return ClientProfile.objects.select_related('user').all()[:limit]
