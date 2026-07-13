"""
Search app signals — update Elasticsearch indices on model changes.

All signal handlers catch ConnectionError defensively so the application
continues to function when Elasticsearch is unavailable (e.g. local dev
without a running ES instance).  Failures are logged at WARNING level so
they remain visible without crashing user-facing requests.
"""

import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.projects.models import Project, ProjectSkill
from apps.users.models import FreelancerProfile
from apps.search.documents import ProjectDocument, FreelancerDocument
logger = logging.getLogger(__name__)


def _es_enabled() -> bool:
    """Return True only when Elasticsearch sync is explicitly enabled."""
    from django.conf import settings
    return getattr(settings, "ELASTICSEARCH_DSL_AUTOSYNC", True)


def _es_update(document_cls, instance, *, label: str) -> None:
    """Best-effort ES index update — logs but never raises on connection errors."""
    if not _es_enabled():
        return
    try:
        document_cls().update(instance)
    except Exception as exc:
        # Catches elastic_transport.ConnectionError, ES exceptions, etc.
        logger.warning(
            "Elasticsearch update skipped for %s (pk=%s): %s",
            label,
            getattr(instance, "pk", "?"),
            exc,
        )


def _es_delete(document_cls, instance, *, label: str) -> None:
    """Best-effort ES index delete — logs but never raises on connection errors."""
    if not _es_enabled():
        return
    try:
        document_cls().delete(instance, ignore=404)
    except Exception as exc:
        logger.warning(
            "Elasticsearch delete skipped for %s (pk=%s): %s",
            label,
            getattr(instance, "pk", "?"),
            exc,
        )


# ── Project signals ───────────────────────────────────────────────────────────

@receiver(post_save, sender=Project)
def update_project_document(sender, instance, **kwargs):
    """Update project document in Elasticsearch when a project is saved."""
    _es_update(ProjectDocument, instance, label="Project")


@receiver(post_delete, sender=Project)
def delete_project_document(sender, instance, **kwargs):
    """Delete project document from Elasticsearch when a project is deleted."""
    _es_delete(ProjectDocument, instance, label="Project")


@receiver(post_save, sender=ProjectSkill)
def update_project_document_on_skill_change(sender, instance, **kwargs):
    """Update project document in Elasticsearch when project skills change."""
    _es_update(ProjectDocument, instance.project, label="Project (skill change)")


@receiver(post_delete, sender=ProjectSkill)
def delete_project_document_on_skill_delete(sender, instance, **kwargs):
    """Update project document in Elasticsearch when a project skill is removed."""
    _es_update(ProjectDocument, instance.project, label="Project (skill delete)")


# ── Freelancer signals ────────────────────────────────────────────────────────

@receiver(post_save, sender=FreelancerProfile)
def update_freelancer_document(sender, instance, **kwargs):
    """Update freelancer document in Elasticsearch when a profile is saved."""
    _es_update(FreelancerDocument, instance, label="FreelancerProfile")


@receiver(post_delete, sender=FreelancerProfile)
def delete_freelancer_document(sender, instance, **kwargs):
    """Delete freelancer document from Elasticsearch when a profile is deleted."""
    _es_delete(FreelancerDocument, instance, label="FreelancerProfile")
