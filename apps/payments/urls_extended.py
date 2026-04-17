"""
URL Configuration for Extended Payment Features
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_extended import PaymentMilestoneViewSet

router = DefaultRouter()
router.register(r'milestones', PaymentMilestoneViewSet, basename='milestone')

urlpatterns = [
    path('', include(router.urls)),
]
