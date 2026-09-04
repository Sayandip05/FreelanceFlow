import logging
from celery import shared_task
from django.apps import apps
from apps.search.documents import ProjectDocument, FreelancerDocument

logger = logging.getLogger(__name__)

DOCUMENT_MAP = {
    'Project': ProjectDocument,
    'FreelancerProfile': FreelancerDocument,
}

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 min before retry
    queue="freelanceflow_low_priority",
)
def update_es_document_task(self, model_name: str, app_label: str, instance_id: int, label: str):
    """
    Async Celery task to update an Elasticsearch document.
    """
    try:
        model = apps.get_model(app_label, model_name)
        instance = model.objects.get(pk=instance_id)
        
        document_cls = DOCUMENT_MAP.get(model_name)
        if not document_cls:
            logger.error("No document class mapping found for model %s", model_name)
            return
            
        document_cls().update(instance)
        logger.info("Elasticsearch async update successful for %s (pk=%s)", label, instance_id)
    except model.DoesNotExist:
        logger.warning("Elasticsearch async update skipped for %s (pk=%s): instance deleted", label, instance_id)
    except Exception as exc:
        logger.warning("Elasticsearch async update failed for %s (pk=%s): %s", label, instance_id, exc)
        raise self.retry(exc=exc)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="freelanceflow_low_priority",
)
def delete_es_document_task(self, model_name: str, instance_id: int, label: str):
    """
    Async Celery task to delete an Elasticsearch document.
    We pass a dummy instance to the delete method since the actual DB instance might be gone.
    """
    try:
        document_cls = DOCUMENT_MAP.get(model_name)
        if not document_cls:
            logger.error("No document class mapping found for model %s", model_name)
            return

        # Correctly delete document by id in Elasticsearch without needing model instance
        document_cls(meta={"id": instance_id}).delete(ignore=404)
        logger.info("Elasticsearch async delete successful for %s (pk=%s)", label, instance_id)
    except Exception as exc:
        logger.warning("Elasticsearch async delete failed for %s (pk=%s): %s", label, instance_id, exc)
        raise self.retry(exc=exc)
