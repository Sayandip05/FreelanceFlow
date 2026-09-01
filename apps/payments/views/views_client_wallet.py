from rest_framework import views, permissions, status
from rest_framework.response import Response
from decimal import Decimal
import logging
import uuid
from django.db import transaction
from django.conf import settings
from apps.payments.models import ClientWallet, ClientDeposit, Payment
from apps.payments.services.services import _get_razorpay_client, confirm_escrow_payment
from apps.payments.services.services import fund_milestone_from_wallet_service
from core.exceptions import ValidationError

logger = logging.getLogger("apps.payments.client_wallet")

class ClientWalletDetailView(views.APIView):
    """
    GET /api/payments/client-wallet/
    Get the client's current wallet balance and deposit history.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if request.user.role != 'CLIENT':
            return Response(
                {"error": "Only clients have access to funding wallets."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        wallet, _ = ClientWallet.objects.get_or_create(client=request.user)
        deposits = ClientDeposit.objects.filter(client=request.user)
        
        # Also fetch direct milestone payments made from the wallet (identified by mock order id)
        milestone_payments = Payment.objects.filter(
            contract__bid__project__client=request.user,
            razorpay_order_id__startswith="order_wallet_"
        ).select_related('milestone')
        
        history = []
        for d in deposits:
            history.append({
                "type": "DEPOSIT",
                "id": d.id,
                "amount": float(d.amount),
                "status": d.status,
                "created_at": d.created_at.isoformat(),
                "description": f"Loaded funds via Razorpay"
            })
            
        for p in milestone_payments:
            history.append({
                "type": "PAYMENT",
                "id": p.id,
                "amount": float(p.total_amount),
                "status": "COMPLETED" if p.status == Payment.Status.ESCROWED else p.status,
                "created_at": p.created_at.isoformat(),
                "description": f"Funded Milestone: {p.milestone.title if p.milestone else 'N/A'}"
            })
            
        # Sort history by date descending
        history.sort(key=lambda x: x["created_at"], reverse=True)

        return Response({
            "balance": float(wallet.balance),
            "history": history
        }, status=status.HTTP_200_OK)


class ClientWalletDepositView(views.APIView):
    """
    POST /api/payments/client-wallet/deposit/
    Initiate loading funds into the client's wallet.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.role != 'CLIENT':
            return Response(
                {"error": "Only clients can add funds to wallets."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        amount = request.data.get("amount")
        milestone_id = request.data.get("auto_fund_milestone_id")
        
        if not amount:
            return Response(
                {"error": "Deposit amount is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            amount_dec = Decimal(str(amount))
            if amount_dec <= 0:
                raise ValidationError("Amount must be greater than zero.")
        except Exception:
            return Response(
                {"error": "Invalid deposit amount format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if credentials are mock/placeholder
        key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
        key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
        is_placeholder = (
            not key_id or 
            key_id.startswith("rzp_test_placeholder") or 
            key_id == "your_razorpay_key_id"
        )
        
        razorpay_order = None
        if not is_placeholder:
            try:
                order_data = {
                    'amount': int(amount_dec * 100),  # paise
                    'currency': 'INR',
                    'receipt': f'deposit_{uuid.uuid4().hex[:10]}',
                }
                razorpay_order = _get_razorpay_client().order.create(data=order_data)
            except Exception as e:
                logger.warning("Failed to create Razorpay order for client deposit: %s. Falling back to mock.", e)

        order_id = razorpay_order['id'] if razorpay_order else f"order_dep_{uuid.uuid4().hex[:12]}"
        
        # Save Deposit Request
        ClientDeposit.objects.create(
            client=request.user,
            amount=amount_dec,
            status=ClientDeposit.Status.PENDING,
            razorpay_order_id=order_id,
            auto_fund_milestone_id=milestone_id
        )

        return Response({
            "order_id": order_id,
            "amount": float(amount_dec),
            "is_mock": not razorpay_order
        }, status=status.HTTP_201_CREATED)


class ClientWalletConfirmDepositView(views.APIView):
    """
    POST /api/payments/client-wallet/deposit/confirm/
    Verify and confirm payment for loading wallet balance.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = request.data.get("razorpay_order_id")
        payment_id = request.data.get("razorpay_payment_id")
        
        if not order_id or not payment_id:
            return Response(
                {"error": "Order ID and Payment ID are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            deposit = ClientDeposit.objects.get(razorpay_order_id=order_id, client=request.user)
        except ClientDeposit.DoesNotExist:
            return Response(
                {"error": "Deposit transaction not found."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        if deposit.status != ClientDeposit.Status.PENDING:
            return Response(
                {"error": "Deposit has already been processed."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        with transaction.atomic():
            # Update deposit status
            deposit.status = ClientDeposit.Status.COMPLETED
            deposit.razorpay_payment_id = payment_id
            deposit.save()
            
            # Lock wallet & update balance
            wallet, _ = ClientWallet.objects.select_for_update().get_or_create(client=request.user)
            wallet.balance += deposit.amount
            wallet.save()
            
            # If this deposit was triggered by a "Top-up & Pay" flow, automatically fund the milestone
            if deposit.auto_fund_milestone:
                milestone = deposit.auto_fund_milestone
                if wallet.balance >= milestone.amount:
                    fund_milestone_from_wallet_service(milestone, request.user)
                    logger.info("Automatically funded milestone %s after top-up deposit %s", milestone.id, deposit.id)
                    
        return Response({
            "message": "Deposit confirmed successfully and wallet balance updated.",
            "balance": float(wallet.balance)
        }, status=status.HTTP_200_OK)


class DownloadTransactionReceiptView(views.APIView):
    """
    GET /api/payments/transactions/<id>/receipt/?type=<deposit|withdrawal|payment>&access=<jwt_token>
    Generates and downloads a styled PDF transaction receipt.
    Allows token in query string so browser can download directly.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, id, *args, **kwargs):
        # If the browser is opening this in a new tab, it won't have the Authorization header.
        # We can accept the token from the query string instead.
        token = request.query_params.get("access")
        if not request.user.is_authenticated and token:
            from rest_framework_simplejwt.authentication import JWTAuthentication
            try:
                validated_token = JWTAuthentication().get_validated_token(token)
                request.user = JWTAuthentication().get_user(validated_token)
            except Exception:
                pass

        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required to download receipt."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        tx_type = request.query_params.get("type", "payment").lower()
        
        # Load transaction details based on type
        amount = 0.0
        tx_id = f"TXN-{id}"
        date_str = ""
        description = ""
        user_name = request.user.get_full_name() or request.user.email
        
        if tx_type == "deposit":
            try:
                deposit = ClientDeposit.objects.get(id=id, client=request.user)
                amount = float(deposit.amount)
                date_str = deposit.created_at.strftime("%Y-%m-%d %H:%M:%S")
                description = f"Wallet Deposit (Order: {deposit.razorpay_order_id})"
                tx_id = f"DEP-{deposit.id}"
            except ClientDeposit.DoesNotExist:
                return Response({"error": "Deposit transaction not found."}, status=status.HTTP_404_NOT_FOUND)
                
        elif tx_type == "withdrawal":
            try:
                withdrawal = WithdrawalRequest.objects.get(id=id, freelancer=request.user)
                amount = float(withdrawal.amount)
                date_str = withdrawal.created_at.strftime("%Y-%m-%d %H:%M:%S")
                description = f"Wallet Withdrawal (Payout: {withdrawal.razorpay_payout_id or 'Simulated'})"
                tx_id = f"WTH-{withdrawal.id}"
            except WithdrawalRequest.DoesNotExist:
                return Response({"error": "Withdrawal transaction not found."}, status=status.HTTP_404_NOT_FOUND)
                
        else:
            try:
                payment = Payment.objects.get(id=id)
                # Verify that either the client or freelancer belongs to this contract
                if payment.contract.client != request.user and payment.contract.bid.freelancer != request.user:
                    return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)
                amount = float(payment.total_amount)
                date_str = payment.created_at.strftime("%Y-%m-%d %H:%M:%S")
                description = f"Milestone Escrow Funding: {payment.milestone.title if payment.milestone else 'Project Milestone'}"
                tx_id = f"PAY-{payment.id}"
            except Payment.DoesNotExist:
                return Response({"error": "Payment transaction not found."}, status=status.HTTP_404_NOT_FOUND)

        # Generate styled HTML for WeasyPrint
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; margin: 40px; }}
                .receipt-box {{ border: 1px solid #eee; padding: 30px; border-radius: 10px; max-width: 800px; margin: auto; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #1e3a8a; }}
                .title {{ font-size: 20px; font-weight: bold; color: #3b82f6; text-align: right; }}
                .details-table {{ width: 100%; margin-top: 30px; border-collapse: collapse; }}
                .details-table th, .details-table td {{ text-align: left; padding: 12px; border-bottom: 1px solid #eee; }}
                .details-table th {{ background-color: #f8fafc; font-weight: bold; color: #475569; }}
                .total-box {{ margin-top: 30px; text-align: right; font-size: 18px; font-weight: bold; color: #1e3a8a; }}
                .footer {{ margin-top: 50px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #eee; padding-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="receipt-box">
                <table style="width: 100%;">
                    <tr>
                        <td>
                            <div class="logo">Freelance<span style="color:#3b82f6;">Flow</span></div>
                            <div style="font-size: 12px; color: #64748b; margin-top: 5px;">Secure Platform Payouts</div>
                        </td>
                        <td style="text-align: right;">
                            <div class="title">TRANSACTION RECEIPT</div>
                            <div style="font-size: 12px; color: #64748b; margin-top: 5px;">Invoice ID: {tx_id}</div>
                        </td>
                    </tr>
                </table>
                
                <hr style="border: 0; border-top: 2px solid #3b82f6; margin: 20px 0;">

                <table style="width: 100%; font-size: 14px; color: #475569;">
                    <tr>
                        <td>
                            <strong>Billed To:</strong><br>
                            {user_name}<br>
                            Platform Account ID: {request.user.id}
                        </td>
                        <td style="text-align: right;">
                            <strong>Transaction Details:</strong><br>
                            Date: {date_str}<br>
                            Gateway: Razorpay Escrow
                        </td>
                    </tr>
                </table>

                <table class="details-table">
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th style="text-align: right;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>{description}</td>
                            <td style="text-align: right; font-weight: bold;">${amount:.2f} USD</td>
                        </tr>
                    </tbody>
                </table>

                <div class="total-box">
                    Total: ${amount:.2f} USD
                </div>

                <div class="footer">
                    Thank you for choosing FreelanceFlow. If you have any questions, please contact support@freelanceflow.com.<br>
                    This is a computer-generated transaction receipt. No signature required.
                </div>
            </div>
        </body>
        </html>
        """

        try:
            from weasyprint import HTML
            from django.http import HttpResponse
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as target:
                HTML(string=html_content).write_pdf(target.name)
                
                # Read file content to response
                with open(target.name, 'rb') as f:
                    pdf_data = f.read()
                    
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_{tx_id}.pdf"'
            return response
        except Exception as e:
            logger.error("Failed to generate PDF invoice receipt: %s", e)
            return Response({"error": f"Failed to generate receipt PDF: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

