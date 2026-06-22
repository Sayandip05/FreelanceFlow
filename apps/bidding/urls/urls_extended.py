"""
URL Configuration for Extended Bidding Features
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_extended import (
    WorklogApprovalViewSet,
    BidRetractionViewSet,
    CounterOfferViewSet
)

router = DefaultRouter()
router.register(r'worklog-approvals', WorklogApprovalViewSet, basename='worklog-approval')
router.register(r'retractions', BidRetractionViewSet, basename='retraction')
router.register(r'counter-offers', CounterOfferViewSet, basename='counter-offer')

urlpatterns = [
    path('', include(router.urls)),
]
