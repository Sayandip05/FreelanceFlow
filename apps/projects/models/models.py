from django.db import models
from django.conf import settings
class Project(models.Model):
    """
    Project model for client-posted projects.
    """
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
    
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
        limit_choices_to={'role': 'CLIENT'}
    )
    title = models.CharField(max_length=255)
    short_description = models.CharField(
        max_length=300,
        blank=True,
        default="",
        help_text="Short summary shown in search/browse view"
    )
    description = models.TextField()
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Maximum budget for the project"
    )
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def summary(self):
        if self.short_description:
            return self.short_description
        if len(self.description) > 150:
            return self.description[:150] + "..."
        return self.description
    
    class Meta:
        db_table = "projects"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=['status', '-created_at'],
                name='project_status_created_idx'
            ),
            models.Index(
                fields=['client', 'status', '-created_at'],
                name='project_client_status_idx'
            ),
            models.Index(
                fields=['status', 'budget'],
                name='project_status_budget_idx'
            ),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.status})"


class ProjectSkill(models.Model):
    """
    Skills required for a project.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="skills"
    )
    skill_name = models.CharField(max_length=100)
    
    class Meta:
        db_table = "project_skills"
        unique_together = ["project", "skill_name"]
        indexes = [
            models.Index(
                fields=['skill_name'],
                name='project_skill_name_idx'
            ),
        ]
    
    def __str__(self):
        return f"{self.project.title} - {self.skill_name}"
