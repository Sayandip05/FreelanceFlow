from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.payments.views import PaymentViewSet, razorpay_webhook, verify_payment
from apps.payments.views.views_extended import PaymentMilestoneViewSet
from apps.payments.views.views_wallet import WalletDetailView, RequestWithdrawalView
from apps.payments.views.views_client_wallet import (
    ClientWalletDetailView, ClientWalletDepositView,
    ClientWalletConfirmDepositView, DownloadTransactionReceiptView
)

router = DefaultRouter()
router.register(r'milestones', PaymentMilestoneViewSet, basename='milestone')
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    # Webhooks & Standard payments
    path('webhook/', razorpay_webhook, name='razorpay-webhook'),
    path('verify/', verify_payment, name='verify-payment'),
    # Freelancer Wallet
    path('wallet/', WalletDetailView.as_view(), name='wallet-detail'),
    path('wallet/withdraw/', RequestWithdrawalView.as_view(), name='request-withdrawal'),
    # Client Wallet
    path('client-wallet/', ClientWalletDetailView.as_view(), name='client-wallet-detail'),
    path('client-wallet/deposit/', ClientWalletDepositView.as_view(), name='client-wallet-deposit'),
    path('client-wallet/deposit/confirm/', ClientWalletConfirmDepositView.as_view(), name='client-wallet-confirm'),
    # Receipts
    path('transactions/<int:id>/receipt/', DownloadTransactionReceiptView.as_view(), name='download-receipt'),
    path('', include(router.urls)),
]
