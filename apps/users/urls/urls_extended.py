"""
URL Configuration for Extended User Features
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views.views_extended import ActivityLogViewSet, OnlineStatusViewSet
from apps.users.views.views_google_oauth import GoogleOAuthInitView, GoogleOAuthCallbackView

router = DefaultRouter()
router.register(r'activity', ActivityLogViewSet, basename='activity')
router.register(r'status', OnlineStatusViewSet, basename='status')

urlpatterns = [
    path('auth/google/', GoogleOAuthInitView.as_view(), name='google-oauth-init'),
    path('auth/google/callback/', GoogleOAuthCallbackView.as_view(), name='google-oauth-callback'),
    path('', include(router.urls)),
]
