"""URL patterns for Review system."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_review import ReviewViewSet

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = router.urls
