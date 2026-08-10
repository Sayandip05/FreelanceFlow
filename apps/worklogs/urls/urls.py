from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.worklogs.views import (
    WorkLogViewSet,
    WeeklyReportViewSet,
    DeliveryProofViewSet,
    DeliverableViewSet,
    AIChatViewSet,
    FileUploadViewSet,
    ReportScheduleViewSet,
)


from apps.worklogs.views.views_ai import (
    AIContextView,
    AIChatView,
    AIApproveDraftView,
    AIHistoryView,
)


router = DefaultRouter()
router.register(r'logs', WorkLogViewSet, basename='worklog')
router.register(r'reports', WeeklyReportViewSet, basename='weeklyreport')
router.register(r'deliverables', DeliverableViewSet, basename='deliverable')
router.register(r'ai-chat', AIChatViewSet, basename='ai-chat')
router.register(r'upload', FileUploadViewSet, basename='upload')
router.register(r'report-schedule', ReportScheduleViewSet, basename='report-schedule')

urlpatterns = [
    path('ai/context/', AIContextView.as_view(), name='ai-context'),
    path('ai/chat/', AIChatView.as_view(), name='ai-chat'),
    path('ai/approve/', AIApproveDraftView.as_view(), name='ai-approve'),
    path('ai/history/', AIHistoryView.as_view(), name='ai-history'),
    path('', include(router.urls)),
    path('proofs/<int:pk>/', DeliveryProofViewSet.as_view({
        'get': 'retrieve',
        'post': 'generate',
    }), name='deliveryproof'),
]
