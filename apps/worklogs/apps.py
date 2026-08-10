from django.apps import AppConfig


class WorklogsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.worklogs"

    def ready(self):
        import apps.worklogs.signals  # noqa: F401
