from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BidViewSet, ContractViewSet
from .views_review import ReviewViewSet


router = DefaultRouter()
router.register(r'bids', BidViewSet, basename='bid')
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
