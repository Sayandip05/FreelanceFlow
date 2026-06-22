from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.bidding.views import BidViewSet, ContractViewSet, ReviewViewSet


router = DefaultRouter()
router.register(r'bids', BidViewSet, basename='bid')
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
