"""
Search Autocomplete Services
"""
from django.db import transaction
from .models_extended import SearchSuggestion


@transaction.atomic
def record_search_term(term, category=None):
    """Record search term for autocomplete"""
    suggestion, created = SearchSuggestion.objects.get_or_create(
        term=term.lower(),
        defaults={'category': category, 'frequency': 1}
    )
    
    if not created:
        suggestion.frequency += 1
        suggestion.save()
    
    return suggestion


def get_autocomplete_suggestions(query, limit=10):
    """Get autocomplete suggestions"""
    return SearchSuggestion.objects.filter(
        term__istartswith=query
    ).order_by('-frequency')[:limit]
