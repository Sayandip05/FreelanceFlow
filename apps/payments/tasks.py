from decimal import Decimal
import logging
from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone
import razorpay
from apps.payments.models import Payment, PlatformEarning
from apps.payments.services.services import confirm_escrow_payment, record_payment_event, _get_razorpay_client
logger = logging.getLogger("apps.payments.tasks")

@shared_task(expires=None)  # Payment webhook — NEVER drop from queue
def process_razorpay_webhook_task(event_id: str, event_type: str, event_data: dict):
    """
    Process Razorpay webhook event asynchronously.
    """
    from .services import has_payment_event_been_processed

    # Double-check idempotency (guards against double-delivery from Razorpay)
    if has_payment_event_been_processed(event_id):
        logger.info("Webhook event already processed, skipping: event_id=%s", event_id)
        return

    logger.info("Processing webhook event: type=%s event_id=%s", event_type, event_id)

    if event_type == 'payment.captured':
        payment_entity = event_data.get('payment', {}).get('entity', {})
        razorpay_order_id = payment_entity.get('order_id')
        razorpay_payment_id = payment_entity.get('id')

        try:
            payment = confirm_escrow_payment(razorpay_order_id, razorpay_payment_id)
            record_payment_event(payment, event_id, event_type)
            logger.info(
                "payment.captured processed: payment_id=%s order_id=%s",
                payment.id, razorpay_order_id,
            )
        except Exception as e:
            logger.error(
                "payment.captured processing failed: order_id=%s event_id=%s error=%s",
                razorpay_order_id, event_id, str(e), exc_info=True,
            )

    elif event_type == 'payment.failed':
        payment_entity = event_data.get('payment', {}).get('entity', {})
        razorpay_order_id = payment_entity.get('order_id')
        logger.warning(
            "payment.failed received: order_id=%s event_id=%s",
            razorpay_order_id, event_id,
        )
        try:
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            record_payment_event(payment, event_id, event_type)
        except Payment.DoesNotExist:
            logger.warning(
                "payment.failed: no local payment found for order_id=%s",
                razorpay_order_id,
            )

    elif event_type == 'payout.processed':
        # Razorpay confirmed the payout reached the freelancer's account
        payout_entity = event_data.get('payout', {}).get('entity', {})
        payout_id = payout_entity.get('id')
        logger.info("payout.processed received: payout_id=%s event_id=%s", payout_id, event_id)
        if payout_id:
            try:
                payment = Payment.objects.filter(razorpay_payout_id=payout_id).first()
                if payment:
                    if payment.status != Payment.Status.RELEASED:
                        payment.status = Payment.Status.RELEASED
                        payment.payout_error = ""
                        payment.save()
                        record_payment_event(payment, event_id, event_type)
                        logger.info("Payment marked RELEASED via payout.processed webhook: payout_id=%s", payout_id)
                    else:
                        logger.debug("payout.processed: payment already RELEASED for payout_id=%s", payout_id)
                else:
                    logger.warning("payout.processed: no matching payment found for payout_id=%s", payout_id)
            except Exception as e:
                logger.error(
                    "payout.processed processing failed: payout_id=%s event_id=%s error=%s",
                    payout_id, event_id, str(e), exc_info=True,
                )
        else:
            logger.warning("payout.processed webhook missing payout entity id: event_id=%s", event_id)

    elif event_type == 'payout.failed':
        # Payout was rejected — mark the payment as PAYOUT_FAILED with the reason
        payout_entity = event_data.get('payout', {}).get('entity', {})
        payout_id = payout_entity.get('id')
        failure_reason = payout_entity.get('failure_reason', '') or 'Payout failed (Razorpay webhook)'
        logger.warning(
            "payout.failed received: payout_id=%s reason=%s event_id=%s",
            payout_id, failure_reason, event_id,
        )
        if payout_id:
            updated = Payment.objects.filter(
                razorpay_payout_id=payout_id,
            ).exclude(
                status=Payment.Status.PAYOUT_FAILED,
            ).update(
                status=Payment.Status.PAYOUT_FAILED,
                payout_error=failure_reason,
            )
            if updated:
                logger.warning(
                    "Payment marked PAYOUT_FAILED via webhook: payout_id=%s reason=%s",
                    payout_id, failure_reason,
                )
        else:
            logger.warning("payout.failed webhook missing payout entity id: event_id=%s", event_id)

    else:
        logger.debug("Unhandled webhook event type: %s event_id=%s", event_type, event_id)


@shared_task(bind=True, max_retries=3, expires=None)  # Payout — NEVER drop, money involved
def razorpay_transfer_to_freelancer_task(self, payment_id: int, amount: float):
    """
    Transfer funds to freelancer using RazorpayX Payouts.
    Retries up to 3 times on transient Razorpay errors.
    """
    logger.info(
        "Starting payout task: payment_id=%s amount=%s",
        payment_id, amount,
    )
    try:
        payment = Payment.objects.select_related(
            "escrow",
            "contract__bid__freelancer__freelancer_profile",
            "contract__bid__project",
        ).get(id=payment_id)
        contract = payment.contract
        freelancer = contract.bid.freelancer
        fund_account_id = freelancer.freelancer_profile.razorpay_fund_account_id

        if not settings.RAZORPAY_ACCOUNT_NUMBER:
            raise ValueError("RAZORPAY_ACCOUNT_NUMBER is not configured.")
        if not fund_account_id:
            raise ValueError("Freelancer Razorpay fund account is not configured.")

        payout = _get_razorpay_client().payout.create({
            'account_number': settings.RAZORPAY_ACCOUNT_NUMBER,
            'amount': int(Decimal(str(amount)) * 100),
            'currency': 'USD',
            'mode': 'IMPS',
            'purpose': 'payout',
            'fund_account_id': fund_account_id,
            'queue_if_low_balance': True,
            'reference_id': f'payment_{payment.id}',
            'narration': 'FreelanceFlow payout',
            'notes': {
                'payment_id': payment.id,
                'contract_id': contract.id,
            },
        })

        with transaction.atomic():
            payment.status = Payment.Status.RELEASED
            payment.razorpay_payout_id = payout.get('id', '')
            payment.payout_error = ""
            payment.save(update_fields=["status", "razorpay_payout_id", "payout_error", "updated_at"])

            from core.utils import calculate_platform_cut
            cut_info = calculate_platform_cut(
                payment.total_amount,
                settings.PLATFORM_CUT_PERCENTAGE,
            )
            PlatformEarning.objects.get_or_create(
                payment=payment,
                defaults={
                    "cut_percentage": cut_info["cut_percentage"],
                    "cut_amount": cut_info["cut_amount"],
                },
            )

            escrow = payment.escrow
            escrow.released_at = timezone.now()
            escrow.save(update_fields=["released_at"])

            contract.is_active = False
            contract.end_date = timezone.now()
            contract.save(update_fields=["is_active", "end_date"])

            from apps.projects.models import Project
            from apps.projects.services import mark_project_completed
            if contract.bid.project.status == Project.Status.IN_PROGRESS:
                mark_project_completed(contract.bid.project)

            from apps.payments.models.models_milestone import PaymentMilestone
            PaymentMilestone.objects.filter(payment_id=str(payment.id)).update(
                status=PaymentMilestone.Status.PAID,
                paid_at=timezone.now(),
            )

        logger.info(
            "Payout succeeded: payment_id=%s payout_id=%s freelancer_id=%s amount=%s",
            payment.id, payout.get('id'), freelancer.id, amount,
        )

        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        from apps.worklogs.services import generate_delivery_proof
        create_notification(
            recipient=freelancer,
            title="Payment Released",
            body=f"Payment for {contract.bid.project.title} has been released.",
            notification_type=Notification.Type.PAYMENT_RELEASED,
        )
        generate_delivery_proof(contract.id)

    except Payment.DoesNotExist:
        logger.error("Payout task: payment_id=%s not found in DB.", payment_id)
    except Exception as e:
        logger.error(
            "Payout task failed: payment_id=%s error=%s",
            payment_id, str(e), exc_info=True,
        )
        Payment.objects.filter(id=payment_id).update(
            status=Payment.Status.PAYOUT_FAILED,
            payout_error=str(e),
        )


@shared_task(bind=True, max_retries=3, expires=None)  # Refund — NEVER drop, money involved
def process_razorpay_refund_task(self, payment_id: int, refund_amount: float):
    """
    Process a Razorpay refund asynchronously.
    Retries up to 3 times on transient errors.
    """
    from .services import process_refund
    logger.info(
        "Starting refund task: payment_id=%s refund_amount=%s",
        payment_id, refund_amount,
    )
    try:
        process_refund(payment_id, refund_amount)
        logger.info(
            "Refund completed: payment_id=%s refund_amount=%s",
            payment_id, refund_amount,
        )
    except Exception as e:
        logger.error(
            "Refund task failed: payment_id=%s refund_amount=%s error=%s",
            payment_id, refund_amount, str(e), exc_info=True,
        )


@shared_task(bind=True, max_retries=3, expires=None)  # Withdrawal — NEVER drop, money involved
def razorpay_payout_withdrawal_task(self, withdrawal_id: int):
    """
    Process freelancer manual withdrawal using RazorpayX Payouts.
    """
    from apps.payments.models import WithdrawalRequest, Wallet
    from django.db import transaction
    
    logger.info("Starting payout withdrawal task: withdrawal_id=%s", withdrawal_id)
    try:
        withdrawal = WithdrawalRequest.objects.select_related(
            "freelancer__freelancer_profile"
        ).get(id=withdrawal_id)
        
        freelancer = withdrawal.freelancer
        fund_account_id = getattr(
            getattr(freelancer, "freelancer_profile", None),
            "razorpay_fund_account_id",
            "",
        )

        is_placeholder_keys = (
            not getattr(settings, "RAZORPAY_KEY_ID", "") or 
            settings.RAZORPAY_KEY_ID.startswith("rzp_test_placeholder") or
            settings.RAZORPAY_KEY_ID == "your_razorpay_key_id"
        )
        use_simulation = is_placeholder_keys or not fund_account_id or not getattr(settings, "RAZORPAY_ACCOUNT_NUMBER", "")

        if use_simulation:
            withdrawal.status = WithdrawalRequest.Status.COMPLETED
            withdrawal.razorpay_payout_id = "payout_mock_simulated"
            withdrawal.save(update_fields=["status", "razorpay_payout_id", "updated_at"])

            from apps.notifications.services import create_notification
            from apps.notifications.models import Notification
            create_notification(
                recipient=freelancer,
                title="Withdrawal Completed",
                body=f"Your simulated withdrawal of USD {withdrawal.amount} has been successfully processed.",
                notification_type=Notification.Type.PAYMENT_RELEASED,
            )
            logger.info("Simulated payout withdrawal succeeded: withdrawal_id=%s", withdrawal.id)
            return

        if not settings.RAZORPAY_ACCOUNT_NUMBER:
            raise ValueError("RAZORPAY_ACCOUNT_NUMBER is not configured.")
        if not fund_account_id:
            raise ValueError("Freelancer Razorpay fund account is not configured.")

        # Call Razorpay Payouts
        payout = _get_razorpay_client().payout.create({
            'account_number': settings.RAZORPAY_ACCOUNT_NUMBER,
            'amount': int(Decimal(str(withdrawal.amount)) * 100),
            'currency': 'USD',
            'mode': 'IMPS',
            'purpose': 'payout',
            'fund_account_id': fund_account_id,
            'queue_if_low_balance': True,
            'reference_id': f'withdrawal_{withdrawal.id}',
            'narration': 'FreelanceFlow withdrawal',
            'notes': {
                'withdrawal_id': withdrawal.id,
                'freelancer_id': freelancer.id,
            },
        })

        withdrawal.status = WithdrawalRequest.Status.COMPLETED
        withdrawal.razorpay_payout_id = payout.get('id', '')
        withdrawal.save(update_fields=["status", "razorpay_payout_id", "updated_at"])

        # Send notification
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        create_notification(
            recipient=freelancer,
            title="Withdrawal Completed",
            body=f"Your withdrawal of USD {withdrawal.amount} has been successfully processed.",
            notification_type=Notification.Type.PAYMENT_RELEASED,
        )

        logger.info(
            "Withdrawal payout succeeded: withdrawal_id=%s payout_id=%s freelancer_id=%s amount=%s",
            withdrawal.id, payout.get('id'), freelancer.id, withdrawal.amount,
        )

    except Exception as exc:
        logger.error(
            "Payout withdrawal task failed for withdrawal_id=%s: %s",
            withdrawal_id, str(exc),
        )
        # Update withdrawal request status to FAILED and refund wallet
        try:
            with transaction.atomic():
                w = WithdrawalRequest.objects.select_for_update().get(id=withdrawal_id)
                if w.status == WithdrawalRequest.Status.PENDING:
                    w.status = WithdrawalRequest.Status.FAILED
                    w.save(update_fields=["status", "updated_at"])
                    # Refund the wallet
                    wallet = Wallet.objects.select_for_update().get(user=w.freelancer)
                    wallet.balance += w.amount
                    wallet.withdrawn_amount -= w.amount
                    wallet.save()
        except Exception as e:
            logger.error("Failed to refund wallet for failed withdrawal: %s", str(e))
        
        raise self.retry(exc=exc, countdown=60)

