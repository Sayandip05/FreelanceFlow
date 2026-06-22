"""
Project Category Services
"""
from django.db import transaction
from .models_extended import ProjectCategory


@transaction.atomic
def create_category(name, slug, description=None, icon=None):
    """Create a project category"""
    return ProjectCategory.objects.create(
        name=name,
        slug=slug,
        description=description,
        icon=icon
    )


def get_all_categories():
    """Get all project categories"""
    return ProjectCategory.objects.all().order_by('name')


def get_category_by_slug(slug):
    """Get category by slug"""
    return ProjectCategory.objects.get(slug=slug)
