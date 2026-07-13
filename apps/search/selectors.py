import logging

from elasticsearch_dsl import Q
from apps.search.documents import ProjectDocument, FreelancerDocument

logger = logging.getLogger(__name__)


def get_project_suggestions(query: str, limit: int = 5) -> list[dict]:
    """
    Get autocomplete-style project suggestions from Elasticsearch.

    Args:
        query: Partial query text.
        limit: Maximum number of suggestions.

    Returns:
        List of project title suggestions.
    """
    search = ProjectDocument.search()
    search = search.query(
        Q("match_phrase_prefix", title={"query": query, "max_expansions": 10})
    )
    search = search.filter("term", status="OPEN")
    search = search.source(["id", "title", "budget", "skills"])

    try:
        response = search[:limit].execute()
        return [hit.to_dict() for hit in response]
    except Exception as e:
        logger.error("Project suggestion query failed: %s", str(e))
        return []


def get_freelancer_suggestions(query: str, limit: int = 5) -> list[dict]:
    """
    Get autocomplete-style freelancer suggestions from Elasticsearch.

    Args:
        query: Partial query text.
        limit: Maximum number of suggestions.

    Returns:
        List of freelancer profile suggestions.
    """
    search = FreelancerDocument.search()
    search = search.query(
        Q("match_phrase_prefix", full_name={"query": query, "max_expansions": 10})
    )
    search = search.source(["id", "full_name", "skills", "hourly_rate"])

    try:
        response = search[:limit].execute()
        return [hit.to_dict() for hit in response]
    except Exception as e:
        logger.error("Freelancer suggestion query failed: %s", str(e))
        return []


def get_similar_projects(project_id: int, limit: int = 5) -> list[dict]:
    """
    Find projects similar to a given project using Elasticsearch MLT query.

    Args:
        project_id: The source project ID.
        limit: Maximum number of similar projects.

    Returns:
        List of similar project dictionaries.
    """
    search = ProjectDocument.search()
    search = search.query(
        Q(
            "more_like_this",
            fields=["title", "description", "skills"],
            like=[{"_index": "projects", "_id": str(project_id)}],
            min_term_freq=1,
            max_query_terms=12,
        )
    )
    search = search.filter("term", status="OPEN")

    try:
        response = search[:limit].execute()
        return [hit.to_dict() for hit in response]
    except Exception as e:
        logger.error("Similar projects query failed: %s", str(e))
        return []


def get_top_freelancers_by_skill(skill: str, limit: int = 10) -> list[dict]:
    """
    Get top-rated freelancers for a specific skill.

    Args:
        skill: Skill name to filter by.
        limit: Maximum number of results.

    Returns:
        List of freelancer profile dictionaries sorted by earnings.
    """
    search = FreelancerDocument.search()
    search = search.filter("term", skills=skill)
    search = search.sort("-total_earned")

    try:
        response = search[:limit].execute()
        return [hit.to_dict() for hit in response]
    except Exception as e:
        logger.error("Top freelancers query failed: %s", str(e))
        return []
