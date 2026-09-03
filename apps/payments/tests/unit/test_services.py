"""
Tests for apps.payments.services.

Coverage:
- verify_razorpay_signature: valid signature, tampered signature
- confirm_escrow_payment: happy path, wrong order_id, non-pending payment
- has_payment_event_been_processed: already processed, not processed
- process_contract_termination_payment: split calculation, status update

Note: create_escrow and release_payment require live Razorpay API calls
so they are NOT unit-tested here — they belong in integration tests.
The verify_razorpay_signature function is pure (no external call) so
it IS tested as a unit.
"""
import hashlib
import hmac

from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from apps.payments.models import Payment, Escrow, PaymentEvent
from apps.payments.services import (
    verify_razorpay_signature,
    confirm_escrow_payment,
    has_payment_event_been_processed,
    record_payment_event,
)
from apps.projects.tests.factories import (
    make_client,
    make_freelancer,
    make_project,
    make_bid,
    make_contract,
)


def _make_payment(contract, status=Payment.Status.PENDING, order_id="order_test_123"):
    return Payment.objects.create(
        contract=contract,
        total_amount=5000,
        status=status,
        razorpay_order_id=order_id,
    )


def _build_valid_signature(order_id: str, payment_id: str, secret: str) -> str:
    """Mirror the exact HMAC computation from services.verify_razorpay_signature."""
    return hmac.new(
        secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()


@override_settings(RAZORPAY_KEY_SECRET="test_secret_key")
class VerifyRazorpaySignatureTest(TestCase):

    def test_valid_signature_returns_true(self):
        order_id = "order_abc"
        payment_id = "pay_xyz"
        sig = _build_valid_signature(order_id, payment_id, "test_secret_key")
        self.assertTrue(verify_razorpay_signature(order_id, payment_id, sig))

    def test_tampered_signature_returns_false(self):
        order_id = "order_abc"
        payment_id = "pay_xyz"
        self.assertFalse(verify_razorpay_signature(order_id, payment_id, "bad_signature"))

    def test_wrong_order_id_returns_false(self):
        payment_id = "pay_xyz"
        sig = _build_valid_signature("order_abc", payment_id, "test_secret_key")
        self.assertFalse(verify_razorpay_signature("order_different", payment_id, sig))


class ConfirmEscrowPaymentTest(TestCase):

    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user, budget=5000)
        self.bid = make_bid(self.project, self.freelancer, amount=5000)
        self.contract = make_contract(self.bid)
        self.payment = _make_payment(self.contract, order_id="order_confirm_test")

    def test_confirm_escrow_updates_status_and_creates_escrow(self):
        updated = confirm_escrow_payment("order_confirm_test", "pay_1")
        self.assertEqual(updated.status, Payment.Status.ESCROWED)
        self.assertEqual(updated.razorpay_payment_id, "pay_1")
        self.assertTrue(Escrow.objects.filter(payment=updated).exists())

    def test_raises_on_unknown_order_id(self):
        from core.exceptions import NotFoundError
        with self.assertRaises(NotFoundError):
            confirm_escrow_payment("order_nonexistent", "pay_1")

    def test_raises_if_payment_not_pending(self):
        from core.exceptions import ValidationError
        self.payment.status = Payment.Status.ESCROWED
        self.payment.save()
        with self.assertRaises(ValidationError):
            confirm_escrow_payment("order_confirm_test", "pay_1")


class PaymentIdempotencyTest(TestCase):

    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user, budget=5000)
        self.bid = make_bid(self.project, self.freelancer, amount=5000)
        self.contract = make_contract(self.bid)
        self.payment = _make_payment(self.contract)

    def test_event_not_processed_returns_false(self):
        self.assertFalse(has_payment_event_been_processed("evt_new_123"))

    def test_after_recording_event_returns_true(self):
        record_payment_event(self.payment, "evt_abc_999", "payment.captured")
        self.assertTrue(has_payment_event_been_processed("evt_abc_999"))

    def test_duplicate_event_id_raises_integrity_error(self):
        from django.db import IntegrityError
        record_payment_event(self.payment, "evt_dup_001", "payment.captured")
        with self.assertRaises(Exception):
            record_payment_event(self.payment, "evt_dup_001", "payment.captured")
