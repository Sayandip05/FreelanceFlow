from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.payments.views import PaymentViewSet, razorpay_webhook, verify_payment
from apps.payments.views.views_extended import PaymentMilestoneViewSet
from apps.payments.views.views_wallet import WalletDetailView, RequestWithdrawalView

router = DefaultRouter()
router.register(r'milestones', PaymentMilestoneViewSet, basename='milestone')
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    path('webhook/', razorpay_webhook, name='razorpay-webhook'),
    path('verify/', verify_payment, name='verify-payment'),
    path('wallet/', WalletDetailView.as_view(), name='wallet-detail'),
    path('wallet/withdraw/', RequestWithdrawalView.as_view(), name='request-withdrawal'),
    path('', include(router.urls)),
]
