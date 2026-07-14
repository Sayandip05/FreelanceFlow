"""
Alias URL module for /api/contracts/ shorthand.
Maps /api/contracts/ → ContractViewSet list/create
Maps /api/contracts/{pk}/ → ContractViewSet detail/update/delete
"""
from rest_framework.routers import DefaultRouter
from apps.bidding.views import ContractViewSet

router = DefaultRouter()
router.register(r'', ContractViewSet, basename='contract-alias')

urlpatterns = router.urls
