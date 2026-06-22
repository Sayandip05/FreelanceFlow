"""Extended search models - History, Saved Searches, Autocomplete."""
from django.db import models
from apps.users.models import User


class SearchHistory(models.Model):
    """
    User search history.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="search_history"
    )
    query = models.CharField(max_length=255)
    search_type = models.CharField(
        max_length=20,
        choices=[
            ('projects', 'Projects'),
            ('freelancers', 'Freelancers'),
            ('all', 'All')
        ]
    )
    filters = models.JSONField(default=dict, blank=True)
    results_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "search_history"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]
    
    def __str__(self):
        return f"{self.user.email} searched '{self.query}'"


class SavedSearch(models.Model):
    """
    Saved searches for quick re-run.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_searches"
    )
    name = models.CharField(max_length=255)
    query = models.CharField(max_length=255)
    search_type = models.CharField(max_length=20)
    filters = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "saved_searches"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"


class SearchSuggestion(models.Model):
    """
    Autocomplete suggestions for search.
    """
    term = models.CharField(max_length=255, unique=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('skill', 'Skill'),
            ('project', 'Project'),
            ('location', 'Location'),
            ('other', 'Other')
        ]
    )
    popularity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "search_suggestions"
        ordering = ["-popularity"]
        indexes = [
            models.Index(fields=["term"]),
            models.Index(fields=["-popularity"]),
        ]
    
    def __str__(self):
        return self.term
