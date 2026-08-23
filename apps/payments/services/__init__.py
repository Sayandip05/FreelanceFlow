from .services import (
    create_escrow,
    create_milestone_escrow,
    confirm_escrow_payment,
    release_payment,
    verify_razorpay_signature,
    process_razorpay_webhook,
    has_payment_event_been_processed,
    record_payment_event,
    process_contract_termination_payment,
    process_refund,
    initiate_payment_dispute,
    withdraw_funds,
)
from .services_currency import (
    get_exchange_rate,
    convert_currency,
    create_multi_currency_payment,
)
from .services_invoice import (
    generate_invoice_pdf,
    get_invoice_html,
)
from .services_milestone import (
    create_milestone,
    complete_milestone,
    release_milestone_payment,
    get_contract_milestones,
    get_milestone_progress,
    get_upcoming_milestones,
    reject_milestone,
)
from .services_tax import (
    generate_tax_document,
    get_tax_documents,
)

# Re-export Celery task so tests can patch apps.payments.services.process_razorpay_webhook_task
# This import comes last to avoid a circular dependency with tasks → services.
def __getattr__(name):
    if name == "process_razorpay_webhook_task":
        from apps.payments.tasks import process_razorpay_webhook_task
        return process_razorpay_webhook_task
    if name == "_get_razorpay_client":
        from apps.payments.services.services import _get_razorpay_client
        return _get_razorpay_client
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
