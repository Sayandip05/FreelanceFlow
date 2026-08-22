from rest_framework import views, permissions, status
from rest_framework.response import Response
from rest_framework import serializers
from decimal import Decimal
from apps.payments.models import Wallet, WithdrawalRequest
from apps.payments.services import withdraw_funds

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance', 'withdrawn_amount', 'created_at', 'updated_at']


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = ['id', 'amount', 'status', 'razorpay_payout_id', 'created_at', 'updated_at']


class WalletDetailView(views.APIView):
    """
    GET /api/payments/wallet/
    Retrieve wallet balance, total withdrawn, and history of withdrawals.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if request.user.role != 'FREELANCER':
            return Response(
                {"error": "Only freelancers have access to wallets."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        withdrawals = WithdrawalRequest.objects.filter(freelancer=request.user)
        
        profile = getattr(request.user, 'freelancer_profile', None)
        payout_linked = bool(profile and profile.razorpay_fund_account_id)
        payout_bank_name = profile.payout_bank_name if profile else ""
        payout_masked_account = profile.payout_masked_account if profile else ""
        payout_account_holder = profile.payout_account_holder if profile else ""
        
        wallet_data = WalletSerializer(wallet).data
        wallet_data.update({
            "payout_linked": payout_linked,
            "payout_bank_name": payout_bank_name,
            "payout_masked_account": payout_masked_account,
            "payout_account_holder": payout_account_holder
        })
        
        return Response({
            "wallet": wallet_data,
            "withdrawals": WithdrawalRequestSerializer(withdrawals, many=True).data
        }, status=status.HTTP_200_OK)


class RequestWithdrawalView(views.APIView):
    """
    POST /api/payments/wallet/withdraw/
    Request a manual fund withdrawal.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        amount = request.data.get('amount')
        if not amount:
            return Response(
                {"error": "Withdrawal amount is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount_dec = Decimal(str(amount))
        except Exception:
            return Response(
                {"error": "Invalid withdrawal amount format."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            withdrawal = withdraw_funds(request.user, amount_dec)
            return Response(
                {
                    "message": "Withdrawal request submitted successfully.",
                    "withdrawal": WithdrawalRequestSerializer(withdrawal).data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
