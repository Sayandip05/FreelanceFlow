from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet, razorpay_webhook, verify_payment


router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', razorpay_webhook, name='razorpay-webhook'),
    path('verify/', verify_payment, name='verify-payment'),
]
