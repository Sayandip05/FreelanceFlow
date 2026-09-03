import uuid
from decimal import Decimal
from django.test import TestCase, tag
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User
from apps.projects.models import Project
from apps.bidding.models import Bid, Contract


@tag("integration", "bidding")
class BiddingIntegrationFlowTest(TestCase):
    """
    End-to-end integration test for hiring lifecycle:
    Client creates project -> Multiple freelancers bid -> Client accepts bid
    -> Contract generated -> Competing bids rejected -> Project updated.
    """

    def setUp(self):
        self.client = APIClient()
        self.client_user = User.objects.create_user(
            email=f"client_{uuid.uuid4().hex[:6]}@example.com",
            password="StrongPass@123",
            role="CLIENT",
            is_email_verified=True,
        )
        self.freelancer_1 = User.objects.create_user(
            email=f"fl1_{uuid.uuid4().hex[:6]}@example.com",
            password="StrongPass@123",
            role="FREELANCER",
            is_email_verified=True,
        )
        self.freelancer_2 = User.objects.create_user(
            email=f"fl2_{uuid.uuid4().hex[:6]}@example.com",
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
            title="Design Modern Mobile App UI",
            short_description="Mobile UI/UX project",
            description="Need clean UI design system for mobile.",
            budget=Decimal("1200.00"),
            approx_duration="1 month",
            status=Project.Status.OPEN,
        )

    def test_complete_hiring_and_contract_generation_flow(self):
        # 1. Freelancer 1 submits a bid
        self.client.force_authenticate(user=self.freelancer_1)
        bids_url = reverse("bid-list")
        res1 = self.client.post(bids_url, {
            "project": self.project.id,
            "amount": "800.00",
            "cover_letter": "I have 5 years of Figma design experience.",
        }, format="json")
        self.assertIn(res1.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        bid1_id = res1.data["id"]

        # 2. Duplicate bid prevention: Freelancer 1 tries bidding again on same project
        res_dup = self.client.post(bids_url, {
            "project": self.project.id,
            "amount": "750.00",
            "cover_letter": "Updated cheaper bid.",
        }, format="json")
        self.assertIn(res_dup.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT])

        # 3. Freelancer 2 submits competing bid
        self.client.force_authenticate(user=self.freelancer_2)
        res2 = self.client.post(bids_url, {
            "project": self.project.id,
            "amount": "900.00",
            "cover_letter": "Expert designer here.",
        }, format="json")
        self.assertIn(res2.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        bid2_id = res2.data["id"]

        # 4. Client accepts Freelancer 1's bid
        self.client.force_authenticate(user=self.client_user)
        accept_url = reverse("bid-accept", kwargs={"pk": bid1_id})
        accept_res = self.client.post(accept_url)
        self.assertIn(accept_res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        # 5. Verify database states
        bid1 = Bid.objects.get(id=bid1_id)
        bid2 = Bid.objects.get(id=bid2_id)
        self.assertEqual(bid1.status, Bid.Status.ACCEPTED)
        self.assertEqual(bid2.status, Bid.Status.REJECTED)

        # 6. Verify Contract was created
        contract = Contract.objects.filter(bid=bid1).first()
        self.assertIsNotNone(contract)
        self.assertEqual(contract.status, Contract.Status.ACTIVE)
        self.assertEqual(contract.agreed_amount, Decimal("800.00"))

        # 7. Security: Outsider cannot view contract detail
        self.client.force_authenticate(user=self.outsider_user)
        contract_url = reverse("contract-detail", kwargs={"pk": contract.id})
        outsider_res = self.client.get(contract_url)
        self.assertIn(outsider_res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # 8. Client can view contract detail
        self.client.force_authenticate(user=self.client_user)
        client_contract_res = self.client.get(contract_url)
        self.assertEqual(client_contract_res.status_code, status.HTTP_200_OK)
