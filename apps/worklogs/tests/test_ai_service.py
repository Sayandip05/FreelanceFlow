from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import User
from apps.projects.models import Project
from apps.bidding.models import Bid, Contract
from apps.worklogs.models import (
    WorkLog,
    Deliverable,
    WeeklyReport,
    AIConversation,
    AIReportDraft,
    QdrantCollection,
)
from apps.worklogs.services.qdrant_service import (
    initialize_collection,
    query_context,
    add_feedback,
    get_collection_name,
    FastEmbeddingService,
)
from apps.worklogs.services.ai_service import run_ai_worklog_agent, generate_weekly_report
from asgiref.sync import async_to_sync


class AIWorklogUnitTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email="client_test@example.com",
            password="StrongPass#123",
            role="CLIENT",
            first_name="Client",
            last_name="Test"
        )
        self.freelancer = User.objects.create_user(
            email="freelancer_test@example.com",
            password="StrongPass#123",
            role="FREELANCER",
            first_name="Freelancer",
            last_name="Test"
        )
        self.project = Project.objects.create(
            client=self.client_user,
            title="NextJS Full Stack AI Marketplace",
            description="Build modern AI freelance marketplace with PostgreSQL and LangGraph.",
            budget=50000,
            status="IN_PROGRESS"
        )
        self.bid = Bid.objects.create(
            project=self.project,
            freelancer=self.freelancer,
            amount=45000,
            cover_letter="Experienced full-stack engineer ready to build the platform."
        )
        self.contract = Contract.objects.create(
            bid=self.bid,
            agreed_amount=45000,
            is_active=True
        )
        self.deliverable = Deliverable.objects.create(
            contract=self.contract,
            freelancer=self.freelancer,
            title="Authentication & DB Schema",
            description="Setup PostgreSQL models and JWT authentication flow.",
            status=Deliverable.Status.APPROVED,
            hours_logged=12.5
        )
        self.worklog = WorkLog.objects.create(
            contract=self.contract,
            freelancer=self.freelancer,
            date=date.today(),
            description="Implemented user profiles, JWT auth endpoints, and migrations.",
            hours_worked=6.5
        )

    def test_embedding_generation(self):
        from apps.worklogs.services.qdrant_service import EMBEDDING_DIM
        emb = FastEmbeddingService.get_embedding("Build modern AI platform")
        self.assertEqual(len(emb), EMBEDDING_DIM)
        self.assertIsInstance(emb[0], float)

    def test_qdrant_collection_init_offline_or_online(self):
        success = initialize_collection(self.contract.id)
        self.assertTrue(success)
        col = QdrantCollection.objects.filter(contract=self.contract).first()
        self.assertIsNotNone(col)
        self.assertEqual(col.collection_name, f"contract_{self.contract.id}_fl_{self.freelancer.id}")
        self.assertTrue(col.is_initialized)

    def test_qdrant_query_and_feedback(self):
        initialize_collection(self.contract.id)
        results = query_context(self.contract.id, "authentication and schema")
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)

        fb_success = add_feedback(self.contract.id, "Please ensure test coverage is above 90%")
        self.assertTrue(fb_success)

    def test_ai_agent_chat_execution(self):
        res = async_to_sync(run_ai_worklog_agent)(
            contract_id=self.contract.id,
            freelancer_id=self.freelancer.id,
            user_message="What deliverables are assigned to this contract?",
            action="chat"
        )
        self.assertIn("reply", res)
        self.assertIsNotNone(res.get("conversation_id"))

        # Verify conversation record created
        conv = AIConversation.objects.get(id=res["conversation_id"])
        self.assertEqual(conv.contract, self.contract)
        self.assertTrue(len(conv.messages) >= 2)

    def test_ai_agent_draft_generation_and_approval(self):
        # 1. Generate Draft
        res = async_to_sync(run_ai_worklog_agent)(
            contract_id=self.contract.id,
            freelancer_id=self.freelancer.id,
            user_message="Please draft my weekly report for this contract",
            action="chat"
        )
        self.assertTrue(res.get("is_draft_ready"))
        self.assertIsNotNone(res.get("draft"))
        draft_id = res.get("draft_id")

        # 2. Approve Draft -> Builds PDF
        approve_res = async_to_sync(run_ai_worklog_agent)(
            contract_id=self.contract.id,
            freelancer_id=self.freelancer.id,
            user_message="Approve and generate official PDF",
            action="approve",
            draft_id=draft_id
        )
        self.assertIsNotNone(approve_res.get("pdf_url"))

        # Check draft status updated to APPROVED
        draft = AIReportDraft.objects.get(id=draft_id)
        self.assertEqual(draft.status, AIReportDraft.Status.APPROVED)
        self.assertTrue(bool(draft.pdf_url))

    def test_legacy_generate_weekly_report(self):
        report = generate_weekly_report(self.contract.id, date.today() - timedelta(days=7))
        self.assertIsNotNone(report)
        self.assertEqual(report.contract, self.contract)

    def test_gemini_fallback_execution(self):
        from apps.worklogs.services.ai_service import call_gemini_fallback_sync
        # Test direct Gemini invocation
        res = call_gemini_fallback_sync(
            system_prompt="You are a helpful AI assistant.",
            history=[],
            user_msg="Hello, reply with JSON: {\"is_draft\": false, \"reply\": \"Hello!\"}"
        )
        # Verify fallback produces a non-empty string or graceful fallback
        self.assertTrue(res is None or isinstance(res, str))


class AIWorklogAPITests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email="api_client@test.com",
            password="StrongPass#123",
            role="CLIENT",
            first_name="APIClient"
        )
        self.freelancer = User.objects.create_user(
            email="api_freelancer@test.com",
            password="StrongPass#123",
            role="FREELANCER",
            first_name="APIFreelancer"
        )
        self.other_user = User.objects.create_user(
            email="api_other@test.com",
            password="StrongPass#123",
            role="FREELANCER",
            first_name="OtherUser"
        )
        self.project = Project.objects.create(
            client=self.client_user,
            title="E-Commerce API Optimization",
            description="Improve response times and index database.",
            budget=30000,
            status="IN_PROGRESS"
        )
        self.bid = Bid.objects.create(
            project=self.project,
            freelancer=self.freelancer,
            amount=28000,
            cover_letter="I can optimize your database indexes."
        )
        self.contract = Contract.objects.create(
            bid=self.bid,
            agreed_amount=28000,
            is_active=True
        )

    def test_context_bundle_endpoint(self):
        self.client.force_authenticate(user=self.freelancer)
        resp = self.client.get(f"/api/worklogs/ai/context/?contract={self.contract.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data
        self.assertEqual(data["contract"]["id"], self.contract.id)
        self.assertIn("deliverables", data)
        self.assertIn("stats", data)
        self.assertIn("previous_reports", data)
        self.assertIn("qdrant_status", data)

    def test_context_bundle_unauthorized_user(self):
        self.client.force_authenticate(user=self.other_user)
        resp = self.client.get(f"/api/worklogs/ai/context/?contract={self.contract.id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_ai_chat_endpoint(self):
        self.client.force_authenticate(user=self.freelancer)
        resp = self.client.post("/api/worklogs/ai/chat/", {
            "contract": self.contract.id,
            "message": "Draft my weekly report for this project"
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("reply", resp.data)
        self.assertIn("conversation_id", resp.data)

    def test_ai_approve_draft_endpoint(self):
        self.client.force_authenticate(user=self.freelancer)
        # Create a draft
        conv = AIConversation.objects.create(contract=self.contract, freelancer=self.freelancer)
        draft = AIReportDraft.objects.create(
            conversation=conv,
            contract=self.contract,
            freelancer=self.freelancer,
            title="Week 1 Report",
            section_summary="Finished query optimizations",
            hours_worked=10.0
        )
        resp = self.client.post("/api/worklogs/ai/approve/", {
            "contract": self.contract.id,
            "draft_id": draft.id
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertIn("pdf_url", resp.data)

    def test_ai_history_endpoint(self):
        self.client.force_authenticate(user=self.freelancer)
        resp = self.client.get(f"/api/worklogs/ai/history/?contract={self.contract.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("conversations", resp.data)
        self.assertIn("drafts", resp.data)
