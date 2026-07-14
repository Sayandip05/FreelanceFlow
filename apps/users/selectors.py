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
        QuerySet or list of FreelancerProfile
    """
    queryset = FreelancerProfile.objects.select_related('user').all()

    if skills:
        # skills is a JSONField(default=list). Neither __overlap (PostgreSQL-only)
        # nor __contains (not supported on SQLite) work portably.
        # Evaluate the queryset and filter in Python to stay DB-agnostic.
        skills_lower = [s.lower() for s in skills]
        matching_ids = [
            fp.pk for fp in queryset
            if any(s.lower() in skills_lower for s in (fp.skills or []))
        ]
        queryset = FreelancerProfile.objects.filter(pk__in=matching_ids).select_related('user')

    return queryset[:limit]


def list_clients(limit: int = 50):
    """List clients."""
    return ClientProfile.objects.select_related('user').all()[:limit]
 
