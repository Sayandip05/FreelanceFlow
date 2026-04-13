"""
Structured logging for the Projects app.
"""
import logging

logger = logging.getLogger("apps.projects")


def log_project_created(project):
    logger.info(
        "Project created: id=%s title='%s' client=%s budget=%s",
        project.id, project.title, project.client_id, project.budget,
    )


def log_project_updated(project, updated_fields=None):
    logger.info(
        "Project updated: id=%s fields=%s",
        project.id, updated_fields or "all",
    )


def log_project_status_changed(project, old_status, new_status):
    logger.info(
        "Project status changed: id=%s '%s' -> '%s'",
        project.id, old_status, new_status,
    )


def log_project_deleted(project_id, user_id):
    logger.warning("Project deleted: id=%s by user=%s", project_id, user_id)
