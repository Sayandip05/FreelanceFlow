"""
URL Configuration for Extended User Features
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_extended import TwoFactorAuthViewSet, ActivityLogViewSet, OnlineStatusViewSet

router = DefaultRouter()
router.register(r'2fa', TwoFactorAuthViewSet, basename='2fa')
router.register(r'activity', ActivityLogViewSet, basename='activity')
router.register(r'status', OnlineStatusViewSet, basename='status')

urlpatterns = [
    path('', include(router.urls)),
]
