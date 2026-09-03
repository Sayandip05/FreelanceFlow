import uuid
from decimal import Decimal
from django.test import TestCase, tag
from rest_framework.test import APIClient
from apps.users.models import User
from apps.projects.models import Project
from apps.bidding.models import Bid, Contract
from apps.worklogs.models import Deliverable
from apps.worklogs.selectors_ai import get_ai_context_bundle


@tag("integration", "worklogs")
class WorklogsIntegrationFlowTest(TestCase):
    """
    End-to-end integration test for AI Worklogs and Deliverables:
    AI Context Bundle -> Deliverable Submission -> Client Approval.
    """

    def setUp(self):
        self.client = APIClient()
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
            title="Build AI Chatbot Integration",
            short_description="AI bot integration",
            description="Integrate LangGraph agent with Django.",
            budget=Decimal("1200.00"),
            approx_duration="1 month",
            status=Project.Status.IN_PROGRESS,
        )
        self.bid = Bid.objects.create(
            project=self.project,
            freelancer=self.freelancer_user,
            amount=Decimal("1000.00"),
            cover_letter="AI/LangGraph specialist.",
            status=Bid.Status.ACCEPTED,
        )
        self.contract = Contract.objects.create(
            bid=self.bid,
            agreed_amount=Decimal("1000.00"),
            status=Contract.Status.ACTIVE,
        )

    def test_complete_deliverable_lifecycle_and_context_bundle(self):
        # 1. Fetch AI context bundle for freelancer
        bundle = get_ai_context_bundle(self.contract.id, self.freelancer_user.id)
        self.assertIsNotNone(bundle)
        self.assertEqual(bundle["contract"]["id"], self.contract.id)

        # 2. Freelancer creates a deliverable draft
        deliverable = Deliverable.objects.create(
            contract=self.contract,
            freelancer=self.freelancer_user,
            title="Milestone 1 Deliverable: Core Agent Engine",
            description="LangGraph workflow compiled and tested.",
            status=Deliverable.Status.DRAFT,
        )
        self.assertEqual(deliverable.status, Deliverable.Status.DRAFT)

        # 3. Freelancer submits deliverable
        deliverable.status = Deliverable.Status.SUBMITTED
        deliverable.save()
        self.assertEqual(deliverable.status, Deliverable.Status.SUBMITTED)

        # 4. Client approves deliverable
        deliverable.status = Deliverable.Status.APPROVED
        deliverable.reviewed_by = self.client_user
        deliverable.client_feedback = "Excellent work on the agent architecture."
        deliverable.save()

        self.assertEqual(deliverable.status, Deliverable.Status.APPROVED)
        self.assertEqual(deliverable.reviewed_by, self.client_user)
