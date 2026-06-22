"""Extended models for Projects - Bookmarks, Categories, Drafts."""
from django.db import models
from apps.users.models import User
from .models import Project


class ProjectCategory(models.Model):
    """
    Categories/tags for projects.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "project_categories"
        verbose_name_plural = "Project Categories"
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class ProjectBookmark(models.Model):
    """
    User bookmarks/favorites for projects.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookmarked_projects"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="bookmarks"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "project_bookmarks"
        unique_together = ["user", "project"]
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.user.email} bookmarked {self.project.title}"


class ProjectDraft(models.Model):
    """
    Draft projects (not yet published).
    """
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="project_drafts"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    skills = models.JSONField(default=list, blank=True)
    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "project_drafts"
        ordering = ["-updated_at"]
    
    def __str__(self):
        return f"Draft: {self.title}"


class ProjectShare(models.Model):
    """
    Public sharing links for projects.
    """
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="share_link"
    )
    share_token = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "project_shares"
    
    def __str__(self):
        return f"Share link for {self.project.title}"
