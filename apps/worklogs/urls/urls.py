from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WorkLogViewSet, 
    WeeklyReportViewSet, 
    DeliveryProofViewSet,
    DeliverableViewSet,
    AIChatViewSet,
    FileUploadViewSet,
)


router = DefaultRouter()
router.register(r'logs', WorkLogViewSet, basename='worklog')
router.register(r'reports', WeeklyReportViewSet, basename='weeklyreport')
router.register(r'deliverables', DeliverableViewSet, basename='deliverable')
router.register(r'ai-chat', AIChatViewSet, basename='ai-chat')
router.register(r'upload', FileUploadViewSet, basename='upload')

urlpatterns = [
    path('', include(router.urls)),
    path('proofs/<int:pk>/', DeliveryProofViewSet.as_view({
        'get': 'retrieve',
        'post': 'generate',
    }), name='deliveryproof'),
]
