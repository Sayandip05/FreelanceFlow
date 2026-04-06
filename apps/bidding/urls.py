from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BidViewSet, ContractViewSet


router = DefaultRouter()
router.register(r'bids', BidViewSet, basename='bid')
router.register(r'contracts', ContractViewSet, basename='contract')

urlpatterns = [
    path('', include(router.urls)),
]
