"""
URL Configuration for Extended Project Features
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_extended import ProjectBookmarkViewSet

router = DefaultRouter()
router.register(r'bookmarks', ProjectBookmarkViewSet, basename='bookmark')

urlpatterns = [
    path('', include(router.urls)),
]
