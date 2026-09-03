import uuid
from django.test import TestCase, tag
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User
from apps.notifications.models import Notification


@tag("integration", "notifications")
class NotificationsIntegrationFlowTest(TestCase):
    """
    End-to-end integration test for user notifications:
    Event dispatch -> Feed retrieval -> Single read -> Bulk mark read -> Isolation check.
    """

    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(
            email=f"usera_{uuid.uuid4().hex[:6]}@example.com",
            password="StrongPass@123",
            role="FREELANCER",
            is_email_verified=True,
        )
        self.user_b = User.objects.create_user(
            email=f"userb_{uuid.uuid4().hex[:6]}@example.com",
            password="StrongPass@123",
            role="CLIENT",
            is_email_verified=True,
        )

    def test_notification_delivery_and_read_management_flow(self):
        # 1. System generates notifications for User A (using recipient, body, type)
        n1 = Notification.objects.create(
            recipient=self.user_a,
            title="Proposal Accepted",
            body="Your proposal on Project X was accepted!",
            type=Notification.Type.BID_ACCEPTED,
            is_read=False,
        )
        n2 = Notification.objects.create(
            recipient=self.user_a,
            title="Milestone Funded",
            body="Client funded Milestone 1 ($500).",
            type=Notification.Type.ESCROW_CREATED,
            is_read=False,
        )

        # 2. System generates a notification for User B
        n_b = Notification.objects.create(
            recipient=self.user_b,
            title="New Proposal",
            body="A freelancer submitted a proposal.",
            type=Notification.Type.BID_SUBMITTED,
            is_read=False,
        )

        # 3. User A queries notifications list
        self.client.force_authenticate(user=self.user_a)
        list_url = reverse("notification-list")
        res = self.client.get(list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        results = res.data.get("results") if isinstance(res.data, dict) else res.data
        user_a_ids = [item["id"] for item in results]
        self.assertIn(n1.id, user_a_ids)
        self.assertIn(n2.id, user_a_ids)
        self.assertNotIn(n_b.id, user_a_ids)  # Privacy: User B's notification not visible

        # 4. User A marks n1 as read
        read_url = reverse("notification-mark-read", kwargs={"pk": n1.id})
        read_res = self.client.post(read_url)
        self.assertIn(read_res.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        n1.refresh_from_db()
        self.assertTrue(n1.is_read)

        # 5. User A marks all as read
        bulk_read_url = reverse("notification-mark-all-read")
        bulk_res = self.client.post(bulk_read_url)
        self.assertIn(bulk_res.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        n2.refresh_from_db()
        self.assertTrue(n2.is_read)
