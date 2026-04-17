"""
Shared test fixtures for FreelanceFlow.

Usage:
    All fixtures are auto-discovered by pytest from this conftest.py.
    Use them in any test file across all apps.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.contrib.auth import get_user_model

from apps.projects.models import Project, ProjectSkill
from apps.bidding.models import Bid, Contract
from apps.payments.models import Payment, Escrow
from apps.worklogs.models import WorkLog
from apps.messaging.models import Conversation, Message
from apps.notifications.models import Notification

User = get_user_model()


# ───────────────────────── User fixtures ─────────────────────────

@pytest.fixture
def client_user(db):
    """Create a client user with profile."""
    user = User.objects.create_user(
        email="client@example.com",
        password="TestPass123!",
        first_name="John",
        last_name="Client",
        role="CLIENT",
    )
    return user


@pytest.fixture
def freelancer_user(db):
    """Create a freelancer user with profile."""
    user = User.objects.create_user(
        email="freelancer@example.com",
        password="TestPass123!",
        first_name="Jane",
        last_name="Freelancer",
        role="FREELANCER",
    )
    return user


@pytest.fixture
def second_freelancer(db):
    """Create a second freelancer for multi-bid tests."""
    return User.objects.create_user(
        email="freelancer2@example.com",
        password="TestPass123!",
        first_name="Bob",
        last_name="Developer",
        role="FREELANCER",
    )


@pytest.fixture
def admin_user(db):
    """Create a superuser."""
    return User.objects.create_superuser(
        email="admin@example.com",
        password="AdminPass123!",
        first_name="Admin",
        last_name="User",
    )


# ───────────────────────── Project fixtures ──────────────────────

@pytest.fixture
def project(client_user):
    """Create a project owned by client_user."""
    proj = Project.objects.create(
        client=client_user,
        title="Django REST API Development",
        description="Build a production-grade REST API using Django and DRF.",
        budget=Decimal("5000.00"),
        deadline=date.today() + timedelta(days=30),
        status=Project.Status.OPEN,
    )
    ProjectSkill.objects.create(project=proj, skill_name="Python")
    ProjectSkill.objects.create(project=proj, skill_name="Django")
    ProjectSkill.objects.create(project=proj, skill_name="REST API")
    return proj


@pytest.fixture
def completed_project(client_user):
    """Create a completed project."""
    return Project.objects.create(
        client=client_user,
        title="Completed Project",
        description="A previously completed project.",
        budget=Decimal("3000.00"),
        status=Project.Status.COMPLETED,
    )


# ───────────────────────── Bid fixtures ──────────────────────────

@pytest.fixture
def bid(project, freelancer_user):
    """Create a pending bid on a project."""
    return Bid.objects.create(
        project=project,
        freelancer=freelancer_user,
        amount=Decimal("4500.00"),
        cover_letter="I have 5 years of Django experience and can deliver this in 3 weeks.",
        status=Bid.Status.PENDING,
    )


@pytest.fixture
def accepted_bid(project, freelancer_user):
    """Create an accepted bid."""
    return Bid.objects.create(
        project=project,
        freelancer=freelancer_user,
        amount=Decimal("4500.00"),
        cover_letter="Accepted proposal",
        status=Bid.Status.ACCEPTED,
    )


# ───────────────────────── Contract fixtures ─────────────────────

@pytest.fixture
def contract(accepted_bid):
    """Create an active contract from an accepted bid."""
    return Contract.objects.create(
        bid=accepted_bid,
        agreed_amount=accepted_bid.amount,
        is_active=True,
    )


# ───────────────────────── Payment fixtures ──────────────────────

@pytest.fixture
def payment(contract):
    """Create a pending payment for a contract."""
    return Payment.objects.create(
        contract=contract,
        total_amount=contract.agreed_amount,
        status=Payment.Status.PENDING,
    )


@pytest.fixture
def escrowed_payment(contract):
    """Create a payment in escrow."""
    payment = Payment.objects.create(
        contract=contract,
        total_amount=contract.agreed_amount,
        status=Payment.Status.ESCROWED,
        razorpay_order_id="order_test_123456",
        razorpay_payment_id="pay_test_123456",
    )
    Escrow.objects.create(
        payment=payment,
        held_amount=contract.agreed_amount,
    )
    return payment


# ───────────────────────── Worklog fixtures ──────────────────────

@pytest.fixture
def worklog(contract, freelancer_user):
    """Create a draft worklog entry."""
    return WorkLog.objects.create(
        contract=contract,
        freelancer=freelancer_user,
        hours=Decimal("8.00"),
        description="Implemented user authentication endpoints",
        date=date.today(),
    )


# ───────────────────────── Messaging fixtures ────────────────────

@pytest.fixture
def conversation(contract):
    """Create a conversation for a contract."""
    return Conversation.objects.create(contract=contract)


@pytest.fixture
def message(conversation, freelancer_user):
    """Create a message in a conversation."""
    return Message.objects.create(
        conversation=conversation,
        sender=freelancer_user,
        content="Hi, I've started working on the project.",
    )


# ───────────────────────── Notification fixtures ─────────────────

@pytest.fixture
def notification(client_user):
    """Create a notification for a user."""
    return Notification.objects.create(
        recipient=client_user,
        title="New Bid Received",
        body="A freelancer has submitted a bid on your project.",
        type=Notification.Type.BID_SUBMITTED,
    )


# ───────────────────────── API client fixtures ───────────────────

@pytest.fixture
def api_client():
    """Return a DRF API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, client_user):
    """Return an API client authenticated as the client user."""
    api_client.force_authenticate(user=client_user)
    return api_client


@pytest.fixture
def authenticated_freelancer(api_client, freelancer_user):
    """Return an API client authenticated as the freelancer user."""
    api_client.force_authenticate(user=freelancer_user)
    return api_client


@pytest.fixture
def authenticated_admin(api_client, admin_user):
    """Return an API client authenticated as admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client
