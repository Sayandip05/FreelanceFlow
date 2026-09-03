import uuid
from decimal import Decimal
from django.test import TestCase, tag
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User
from apps.projects.models import Project
from apps.bidding.models import Bid, Contract
from apps.messaging.models import Conversation, Message


@tag("integration", "messaging")
class MessagingIntegrationFlowTest(TestCase):
    """
    End-to-end integration test for contract messaging:
    Conversation creation -> Message exchange -> Unread counts -> Read receipts -> Access boundaries.
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
        self.outsider_user = User.objects.create_user(
            email=f"outsider_{uuid.uuid4().hex[:6]}@example.com",
            password="StrongPass@123",
            role="FREELANCER",
            is_email_verified=True,
        )
        self.project = Project.objects.create(
            client=self.client_user,
            title="Setup Kubernetes Cluster",
            short_description="DevOps setup",
            description="DevOps setup on AWS EKS",
            budget=Decimal("1500.00"),
            approx_duration="1 month",
            status=Project.Status.IN_PROGRESS,
        )
        self.bid = Bid.objects.create(
            project=self.project,
            freelancer=self.freelancer_user,
            amount=Decimal("1200.00"),
            cover_letter="Certified K8s administrator with 6 years experience.",
            status=Bid.Status.ACCEPTED,
        )
        self.contract = Contract.objects.create(
            bid=self.bid,
            agreed_amount=Decimal("1200.00"),
            status=Contract.Status.ACTIVE,
        )

    def test_message_exchange_and_read_receipt_flow(self):
        # 1. Create conversation for contract
        conversation = Conversation.objects.create(contract=self.contract)

        # 2. Client sends a message
        msg1 = Message.objects.create(
            conversation=conversation,
            sender=self.client_user,
            content="Hello! Can you share the repository link?",
        )
        self.assertFalse(msg1.is_read)

        # 3. Freelancer logs in and reads conversation messages
        self.client.force_authenticate(user=self.freelancer_user)
        messages_url = reverse("conversation-messages", kwargs={"pk": conversation.id})
        res = self.client.get(messages_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 4. Freelancer marks messages as read
        read_url = reverse("conversation-mark-read", kwargs={"pk": conversation.id})
        read_res = self.client.post(read_url)
        self.assertIn(read_res.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

        msg1.refresh_from_db()
        self.assertTrue(msg1.is_read)

        # 5. Security: Outsider cannot view conversation
        self.client.force_authenticate(user=self.outsider_user)
        outsider_res = self.client.get(messages_url)
        self.assertIn(outsider_res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
