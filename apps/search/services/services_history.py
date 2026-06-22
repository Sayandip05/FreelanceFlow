"""
Search History Services
"""
from django.db import transaction
from .models_extended import SearchHistory


@transaction.atomic
def log_search(user, query, filters=None, results_count=0):
    """Log a search query"""
    return SearchHistory.objects.create(
        user=user,
        query=query,
        filters=filters or {},
        results_count=results_count
    )


def get_search_history(user, limit=20):
    """Get user's search history"""
    return SearchHistory.objects.filter(user=user).order_by('-created_at')[:limit]


def get_popular_searches(limit=10):
    """Get most popular search queries"""
    from django.db.models import Count
    
    return SearchHistory.objects.values('query').annotate(
        count=Count('id')
    ).order_by('-count')[:limit]
