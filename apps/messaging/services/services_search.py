"""
Message Search Services
"""
from django.db import transaction
from .models_extended import MessageSearch


@transaction.atomic
def index_message(message):
    """Index message for search"""
    from django.contrib.postgres.search import SearchVector
    
    MessageSearch.objects.create(
        message=message,
        conversation=message.conversation,
        search_vector=SearchVector('content')
    )


def search_messages(conversation_id, query):
    """Search messages in a conversation"""
    from django.contrib.postgres.search import SearchQuery
    
    search_query = SearchQuery(query)
    
    return MessageSearch.objects.filter(
        conversation_id=conversation_id,
        search_vector=search_query
    ).select_related('message')
