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
from django.db import transaction
from apps.projects.models import Project, ProjectSkill
from apps.users.models import FreelancerProfile
from apps.search.documents import ProjectDocument, FreelancerDocument
from apps.search.tasks import update_es_document_task, delete_es_document_task
logger = logging.getLogger(__name__)


def _es_enabled() -> bool:
    """Return True only when Elasticsearch sync is explicitly enabled."""
    from django.conf import settings
    return getattr(settings, "ELASTICSEARCH_DSL_AUTOSYNC", True)


def _es_update(model_name: str, app_label: str, instance_id: int, label: str) -> None:
    """Best-effort ES index update via Celery."""
    if not _es_enabled():
        return
    transaction.on_commit(lambda: update_es_document_task.delay(
        model_name=model_name,
        app_label=app_label,
        instance_id=instance_id,
        label=label
    ))


def _es_delete(model_name: str, instance_id: int, label: str) -> None:
    """Best-effort ES index delete via Celery."""
    if not _es_enabled():
        return
    transaction.on_commit(lambda: delete_es_document_task.delay(
        model_name=model_name,
        instance_id=instance_id,
        label=label
    ))


# ── Project signals ───────────────────────────────────────────────────────────

@receiver(post_save, sender=Project)
def update_project_document(sender, instance, **kwargs):
    """
    Elasticsearch project lifecycle:
    - If project is OPEN: index/update in Elasticsearch so freelancers can discover and bid.
    - If project is accepted on both sides (IN_PROGRESS), COMPLETED, or CANCELLED:
      immediately remove/delete from Elasticsearch to free storage and hide taken projects.
    """
    if instance.status == Project.Status.OPEN:
        _es_update("Project", "projects", instance.id, label="Project (OPEN)")
    else:
        _es_delete("Project", instance.id, label=f"Project ({instance.status} - Removed from ES)")


@receiver(post_delete, sender=Project)
def delete_project_document(sender, instance, **kwargs):
    """Delete project document from Elasticsearch when a project is deleted."""
    _es_delete("Project", instance.id, label="Project")


@receiver(post_save, sender=ProjectSkill)
def update_project_document_on_skill_change(sender, instance, **kwargs):
    """Update project document in Elasticsearch when project skills change."""
    _es_update("Project", "projects", instance.project.id, label="Project (skill change)")


@receiver(post_delete, sender=ProjectSkill)
def delete_project_document_on_skill_delete(sender, instance, **kwargs):
    """Update project document in Elasticsearch when a project skill is removed."""
    _es_update("Project", "projects", instance.project.id, label="Project (skill delete)")


# ── Freelancer signals ────────────────────────────────────────────────────────

@receiver(post_save, sender=FreelancerProfile)
def update_freelancer_document(sender, instance, **kwargs):
    """Update freelancer document in Elasticsearch when a profile is saved."""
    _es_update("FreelancerProfile", "users", instance.id, label="FreelancerProfile")


@receiver(post_delete, sender=FreelancerProfile)
def delete_freelancer_document(sender, instance, **kwargs):
    """Delete freelancer document from Elasticsearch when a profile is deleted."""
    _es_delete("FreelancerProfile", instance.id, label="FreelancerProfile")
