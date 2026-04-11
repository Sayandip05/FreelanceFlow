from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with email as username and role field.
    """
    class Roles(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        FREELANCER = "FREELANCER", "Freelancer"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.FREELANCER)
    
    # Account deactivation
    is_deactivated = models.BooleanField(
        default=False,
        help_text="User has deactivated their account (soft delete)"
    )
    deactivated_at = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    
    class Meta:
        db_table = "users"
    
    def __str__(self):
        return f"{self.email} ({self.role})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class FreelancerProfile(models.Model):
    """
    Profile for freelancers with skills, rates, and subscription info.
    """
    class SubscriptionTier(models.TextChoices):
        FREE = "FREE", "Free"
        PRO = "PRO", "Pro"
    
    user = models.OneToOneField(
        "users.User", 
        on_delete=models.CASCADE, 
        related_name="freelancer_profile"
    )
    bio = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    subscription_tier = models.CharField(
        max_length=10,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE
    )
    total_earned = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0
    )
    
    # New fields
    avatar = models.URLField(
        max_length=500,
        blank=True,
        help_text="Profile photo URL"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Whether freelancer is available for new projects"
    )
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0
    )
    total_reviews = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "freelancer_profiles"
    
    def __str__(self):
        return f"Freelancer: {self.user.email}"


class ClientProfile(models.Model):
    """
    Profile for clients with company info and spending tracking.
    """
    user = models.OneToOneField(
        "users.User", 
        on_delete=models.CASCADE, 
        related_name="client_profile"
    )
    company_name = models.CharField(max_length=255, blank=True)
    total_spent = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0
    )
    
    # New fields
    avatar = models.URLField(
        max_length=500,
        blank=True,
        help_text="Profile photo URL"
    )
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0
    )
    total_reviews = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "client_profiles"
    
    def __str__(self):
        return f"Client: {self.user.email}"
