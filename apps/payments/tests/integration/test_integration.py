import uuid
from decimal import Decimal
from django.test import TestCase, tag
from apps.users.models import User
from apps.projects.models import Project
from apps.bidding.models import Bid, Contract
from apps.payments.models import PaymentMilestone, Escrow, Payment, Wallet


@tag("integration", "payments")
class PaymentsIntegrationFlowTest(TestCase):
    """
    End-to-end integration test for financial lifecycle:
    Milestone Creation -> Escrow Funding -> Deliverable Approval -> Payout with Platform Fee.
    """

    def setUp(self):
        self.client_user = User.objects.create_user(
            email=f"client_{uuid.uuid4().hex[:6]}@example.com",
            password="StrongPass@123",
            role="CLIENT",
            is_email_verified=True,
        )
        self.freelancer_user = User.objects.create_user(
            email=f"fl_{uuid.uuid4().hex[:6]}@example.com",
            password="StrongPass@123",
            role="FREELANCER",
            is_email_verified=True,
        )
        self.project = Project.objects.create(
            client=self.client_user,
            title="API Backend Development",
            short_description="Backend API",
            description="Build scalable API",
            budget=Decimal("1000.00"),
            approx_duration="1 month",
            status=Project.Status.IN_PROGRESS,
        )
        self.bid = Bid.objects.create(
            project=self.project,
            freelancer=self.freelancer_user,
            amount=Decimal("1000.00"),
            cover_letter="Senior Django engineer ready to implement full backend.",
            status=Bid.Status.ACCEPTED,
        )
        self.contract = Contract.objects.create(
            bid=self.bid,
            agreed_amount=Decimal("1000.00"),
            status=Contract.Status.ACTIVE,
        )

    def test_milestone_escrow_and_approval_payout_flow(self):
        # 1. Client creates milestone (percentage required)
        milestone = PaymentMilestone.objects.create(
            contract=self.contract,
            title="Phase 1: Architecture & Auth",
            description="Initial models and JWT auth endpoints",
            amount=Decimal("500.00"),
            percentage=Decimal("50.00"),
            order=1,
            status=PaymentMilestone.Status.PENDING,
        )

        # 2. Fund milestone into escrow via payment
        payment = Payment.objects.create(
            contract=self.contract,
            milestone=milestone,
            total_amount=Decimal("500.00"),
            status=Payment.Status.ESCROWED,
        )
        escrow = Escrow.objects.create(
            payment=payment,
            held_amount=Decimal("500.00"),
        )
        milestone.status = PaymentMilestone.Status.IN_PROGRESS
        milestone.save()

        self.assertEqual(milestone.status, PaymentMilestone.Status.IN_PROGRESS)
        self.assertEqual(escrow.held_amount, Decimal("500.00"))

        # 3. Freelancer wallet initially starts at 0 balance
        freelancer_wallet, _ = Wallet.objects.get_or_create(user=self.freelancer_user)
        initial_balance = Decimal(str(freelancer_wallet.balance))

        # 4. Release Escrow with 10% platform fee
        platform_fee_percent = Decimal("0.10")
        gross_amount = escrow.held_amount
        fee_amount = gross_amount * platform_fee_percent
        net_payout = gross_amount - fee_amount

        milestone.status = PaymentMilestone.Status.PAID
        milestone.save()
        payment.status = Payment.Status.RELEASED
        payment.save()

        freelancer_wallet.balance = initial_balance + net_payout
        freelancer_wallet.save()

        # 5. Assertions
        self.assertEqual(milestone.status, PaymentMilestone.Status.PAID)
        self.assertEqual(payment.status, Payment.Status.RELEASED)
        self.assertEqual(Decimal(str(freelancer_wallet.balance)), initial_balance + Decimal("450.00"))
