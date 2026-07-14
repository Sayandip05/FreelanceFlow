"""
Alias URL module for /api/bids/ shorthand.
Maps /api/bids/ → BidViewSet list/create
Maps /api/bids/{pk}/ → BidViewSet detail/update/delete
Maps /api/bids/{pk}/accept/, /reject/, /withdraw/ → custom actions
"""
from rest_framework.routers import DefaultRouter
from apps.bidding.views import BidViewSet

router = DefaultRouter()
router.register(r'', BidViewSet, basename='bid-alias')

urlpatterns = router.urls
