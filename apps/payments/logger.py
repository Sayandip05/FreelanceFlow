"""
Structured logging for the Payments app.
"""
import logging

logger = logging.getLogger("apps.payments")


def log_escrow_created(escrow):
    logger.info(
        "Escrow created: id=%s payment=%s amount=%s",
        escrow.id, escrow.payment_id, escrow.held_amount,
    )


def log_payment_released(payment):
    logger.info(
        "Payment released: id=%s amount=%s contract=%s",
        payment.id, payment.total_amount, payment.contract_id,
    )


def log_payment_refunded(payment):
    logger.warning(
        "Payment refunded: id=%s amount=%s contract=%s",
        payment.id, payment.total_amount, payment.contract_id,
    )


def log_razorpay_webhook_received(event_type, event_id):
    logger.info("Razorpay webhook received: type=%s event_id=%s", event_type, event_id)


def log_razorpay_webhook_failed(event_type, event_id, error):
    logger.error(
        "Razorpay webhook processing failed: type=%s event_id=%s error=%s",
        event_type, event_id, str(error),
    )


def log_platform_earning(earning):
    logger.info(
        "Platform earning: payment=%s cut=%.2f%% amount=%s",
        earning.payment_id, earning.cut_percentage, earning.cut_amount,
    )
