"""
Tests for apps.messaging services and views.
Covers: get_or_create_conversation, send_message, mark_messages_as_read,
        ConversationViewSet list/messages/send/mark_read endpoints.
"""
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import TestCase
from apps.bidding.models import Bid
from apps.messaging.models import Conversation, Message
from apps.messaging.services import get_or_create_conversation, send_message, mark_messages_as_read
from apps.projects.tests.factories import make_client, make_freelancer, make_project, make_bid, make_contract
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError
def auth(user):
    return f"Bearer {RefreshToken.for_user(user).access_token}"


def _setup():
    client_user = make_client()
    freelancer = make_freelancer()
    project = make_project(client_user)
    bid = make_bid(project, freelancer, status=Bid.Status.ACCEPTED)
    contract = make_contract(bid)
    return client_user, freelancer, contract


# ── Service Tests ──────────────────────────────────────────────────────────────

class GetOrCreateConversationTests(TestCase):
    def setUp(self):
        self.client_user, self.freelancer, self.contract = _setup()

    def test_creates_conversation_for_contract(self):
        conv = get_or_create_conversation(self.contract.id)
        self.assertIsInstance(conv, Conversation)
        self.assertEqual(conv.contract, self.contract)

    def test_returns_existing_conversation(self):
        conv1 = get_or_create_conversation(self.contract.id)
        conv2 = get_or_create_conversation(self.contract.id)
        self.assertEqual(conv1.id, conv2.id)

    def test_nonexistent_contract_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            get_or_create_conversation(99999)


class SendMessageTests(TestCase):
    def setUp(self):
        self.client_user, self.freelancer, self.contract = _setup()
        self.conversation = get_or_create_conversation(self.contract.id)

    def test_freelancer_can_send_message(self):
        msg = send_message(self.freelancer, self.conversation.id, "Hello client!")
        self.assertIsInstance(msg, Message)
        self.assertEqual(msg.sender, self.freelancer)
        self.assertEqual(msg.content, "Hello client!")

    def test_client_can_send_message(self):
        msg = send_message(self.client_user, self.conversation.id, "Hello freelancer!")
        self.assertEqual(msg.sender, self.client_user)

    def test_empty_content_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            send_message(self.freelancer, self.conversation.id, "   ")

    def test_outsider_cannot_send_message(self):
        outsider = make_freelancer(email="outsider@test.com")
        with self.assertRaises(PermissionDeniedError):
            send_message(outsider, self.conversation.id, "I should not be here!")

    def test_nonexistent_conversation_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            send_message(self.freelancer, 99999, "Hello!")


class MarkMessagesReadTests(TestCase):
    def setUp(self):
        self.client_user, self.freelancer, self.contract = _setup()
        self.conversation = get_or_create_conversation(self.contract.id)
        # Freelancer sends 2 messages
        send_message(self.freelancer, self.conversation.id, "Message one from freelancer.")
        send_message(self.freelancer, self.conversation.id, "Message two from freelancer.")

    def test_client_marks_freelancer_messages_as_read(self):
        count = mark_messages_as_read(self.conversation.id, self.client_user)
        self.assertEqual(count, 2)
        unread = Message.objects.filter(conversation=self.conversation, is_read=False)
        self.assertEqual(unread.count(), 0)

    def test_idempotent_when_already_read(self):
        mark_messages_as_read(self.conversation.id, self.client_user)
        count = mark_messages_as_read(self.conversation.id, self.client_user)
        self.assertEqual(count, 0)


# ── View Tests ─────────────────────────────────────────────────────────────────

class ConversationViewTests(APITestCase):
    def setUp(self):
        self.client_user, self.freelancer, self.contract = _setup()
        self.conversation = get_or_create_conversation(self.contract.id)

    def test_freelancer_can_list_conversations(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.get("/api/messaging/conversations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_client_can_list_conversations(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.client_user))
        response = self.client.get("/api/messaging/conversations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_list(self):
        response = self.client.get("/api/messaging/conversations/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_freelancer_can_send_message_via_api(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.post(
            f"/api/messaging/conversations/{self.conversation.id}/send/",
            {"content": "Hello from the API!"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "Hello from the API!")

    def test_send_empty_message_returns_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.post(
            f"/api/messaging/conversations/{self.conversation.id}/send/",
            {"content": ""},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mark_read_endpoint(self):
        send_message(self.freelancer, self.conversation.id, "Unread message here.")
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.client_user))
        response = self.client.post(
            f"/api/messaging/conversations/{self.conversation.id}/mark_read/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_messages_for_conversation(self):
        send_message(self.freelancer, self.conversation.id, "Test message content.")
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.client_user))
        response = self.client.get(
            f"/api/messaging/conversations/{self.conversation.id}/messages/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
