"""
Saved Search Services
"""
from django.db import transaction
from .models_extended import SavedSearch


@transaction.atomic
def save_search(user, name, query, filters=None, notification_enabled=False):
    """Save a search query"""
    return SavedSearch.objects.create(
        user=user,
        name=name,
        query=query,
        filters=filters or {},
        notification_enabled=notification_enabled
    )


def get_saved_searches(user):
    """Get user's saved searches"""
    return SavedSearch.objects.filter(user=user).order_by('-created_at')


@transaction.atomic
def delete_saved_search(search_id, user):
    """Delete a saved search"""
    SavedSearch.objects.filter(id=search_id, user=user).delete()
