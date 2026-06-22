import logging

from elasticsearch_dsl import Q

from apps.search.documents import ProjectDocument, FreelancerDocument

logger = logging.getLogger(__name__)


def search_projects(
    query: str = "",
    skills: list[str] | None = None,
    min_budget: float | None = None,
    max_budget: float | None = None,
    status: str = "OPEN",
    limit: int = 50,
) -> list[dict]:
    """
    Search projects using Elasticsearch with filters.

    Args:
        query: Free-text search query.
        skills: Filter by skill names.
        min_budget: Minimum budget filter.
        max_budget: Maximum budget filter.
        status: Project status filter (default: OPEN).
        limit: Maximum number of results.

    Returns:
        List of project dictionaries.
    """
    search = ProjectDocument.search()

    if query:
        search = search.query(
            Q("multi_match", query=query, fields=["title^3", "description", "skills"])
        )

    if skills:
        search = search.filter("terms", skills=skills)

    if min_budget is not None:
        search = search.filter("range", budget={"gte": min_budget})

    if max_budget is not None:
        search = search.filter("range", budget={"lte": max_budget})

    if status:
        search = search.filter("term", status=status)

    # Add highlighting
    search = search.highlight("title", "description")

    try:
        response = search[:limit].execute()
        logger.info("Project search executed: query='%s', results=%d", query, len(response))
        return [hit.to_dict() for hit in response]
    except Exception as e:
        logger.error("Elasticsearch project search failed: %s", str(e))
        return []


def search_freelancers(
    query: str = "",
    skills: list[str] | None = None,
    min_rate: float | None = None,
    max_rate: float | None = None,
    limit: int = 50,
) -> list[dict]:
    """
    Search freelancers using Elasticsearch with filters.

    Args:
        query: Free-text search query.
        skills: Filter by skill names.
        min_rate: Minimum hourly rate filter.
        max_rate: Maximum hourly rate filter.
        limit: Maximum number of results.

    Returns:
        List of freelancer profile dictionaries.
    """
    search = FreelancerDocument.search()

    if query:
        search = search.query(
            Q("multi_match", query=query, fields=["full_name^2", "bio", "skills"])
        )

    if skills:
        search = search.filter("terms", skills=skills)

    if min_rate is not None:
        search = search.filter("range", hourly_rate={"gte": min_rate})

    if max_rate is not None:
        search = search.filter("range", hourly_rate={"lte": max_rate})

    # Add highlighting
    search = search.highlight("full_name", "bio")

    try:
        response = search[:limit].execute()
        logger.info("Freelancer search executed: query='%s', results=%d", query, len(response))
        return [hit.to_dict() for hit in response]
    except Exception as e:
        logger.error("Elasticsearch freelancer search failed: %s", str(e))
        return []


def reindex_all():
    """
    Rebuild all Elasticsearch indexes from the database.
    Useful after data migration or index corruption.
    """
    from django.core.management import call_command

    logger.info("Starting full Elasticsearch reindex...")
    try:
        call_command("search_index", "--rebuild", "-f")
        logger.info("Elasticsearch reindex completed successfully.")
    except Exception as e:
        logger.error("Elasticsearch reindex failed: %s", str(e))
        raise
