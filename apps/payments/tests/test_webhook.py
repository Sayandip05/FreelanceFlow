"""
Tests for Razorpay webhook processing — idempotency and signature verification.

The full async webhook task is NOT tested here (Celery/Redis required).
What IS tested:
- process_razorpay_webhook: rejects invalid signature, handles already-processed events
- has_payment_event_been_processed: database idempotency guard
"""
import json
import hashlib
import hmac

from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from apps.payments.models import Payment, PaymentEvent
from apps.payments.services import (
    process_razorpay_webhook,
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
from core.exceptions import PermissionDeniedError, ValidationError
def _make_payment(contract):
    return Payment.objects.create(
        contract=contract,
        total_amount=5000,
        status=Payment.Status.PENDING,
        razorpay_order_id="order_wh_test",
    )


def _sign_payload(raw_body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()


@override_settings(
    RAZORPAY_KEY_SECRET="wh_test_secret",
    RAZORPAY_WEBHOOK_SECRET="wh_secret_key",
)
class WebhookProcessingTest(TestCase):

    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user, budget=5000)
        self.bid = make_bid(self.project, self.freelancer, amount=5000)
        self.contract = make_contract(self.bid)
        self.payment = _make_payment(self.contract)

    def _build_webhook_payload(self):
        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_xyz",
                        "order_id": "order_wh_test",
                    }
                }
            }
        }
        raw = json.dumps(payload).encode()
        return payload, raw

    @patch("apps.payments.services._get_razorpay_client")
    @patch("apps.payments.services.process_razorpay_webhook_task")
    def test_webhook_with_valid_signature_queues_task(self, mock_task, mock_razorpay):
        """Valid signature and new event_id → task is dispatched."""
        payload, raw = self._build_webhook_payload()
        # _get_razorpay_client() returns a client; configure its return_value.
        mock_razorpay.return_value.utility.verify_webhook_signature.return_value = None
        mock_task.delay = MagicMock()

        result = process_razorpay_webhook(
            payload=payload,
            raw_body=raw,
            signature="valid_sig",
            event_id="evt_unique_001",
        )

        self.assertTrue(result)
        mock_task.delay.assert_called_once()

    @patch("apps.payments.services._get_razorpay_client")
    def test_webhook_with_invalid_signature_raises(self, mock_razorpay):
        import razorpay
        mock_razorpay.return_value.utility.verify_webhook_signature.side_effect = (
            razorpay.errors.SignatureVerificationError("bad", "sig")
        )
        payload, raw = self._build_webhook_payload()
        with self.assertRaises(PermissionDeniedError):
            process_razorpay_webhook(
                payload=payload,
                raw_body=raw,
                signature="tampered_sig",
                event_id="evt_any",
            )

    @patch("apps.payments.services._get_razorpay_client")
    @patch("apps.payments.services.process_razorpay_webhook_task")
    def test_duplicate_event_is_skipped(self, mock_task, mock_razorpay):
        """Already-processed events must be idempotent — task NOT dispatched again."""
        mock_razorpay.return_value.utility.verify_webhook_signature.return_value = None
        mock_task.delay = MagicMock()

        record_payment_event(self.payment, "evt_dup_002", "payment.captured")
        payload, raw = self._build_webhook_payload()

        result = process_razorpay_webhook(
            payload=payload,
            raw_body=raw,
            signature="valid_sig",
            event_id="evt_dup_002",
        )

        self.assertTrue(result)
        mock_task.delay.assert_not_called()

    @patch("apps.payments.services._get_razorpay_client")
    def test_missing_event_id_raises(self, mock_razorpay):
        mock_razorpay.return_value.utility.verify_webhook_signature.return_value = None
        payload, raw = self._build_webhook_payload()
        with self.assertRaises(ValidationError):
            process_razorpay_webhook(
                payload=payload,
                raw_body=raw,
                signature="valid_sig",
                event_id=None,
            )
