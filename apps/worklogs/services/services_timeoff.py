"""
Time-off Tracking Services
"""
from django.db import transaction
from .models_extended import TimeOff


@transaction.atomic
def request_timeoff(freelancer, start_date, end_date, reason=None, contract=None):
    """Request time-off"""
    return TimeOff.objects.create(
        freelancer=freelancer,
        contract=contract,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status=TimeOff.Status.PENDING
    )


@transaction.atomic
def approve_timeoff(timeoff_id, approver):
    """Approve time-off request"""
    timeoff = TimeOff.objects.get(id=timeoff_id)
    timeoff.status = TimeOff.Status.APPROVED
    timeoff.approved_by = approver
    timeoff.approved_at = timezone.now()
    timeoff.save()
    return timeoff


@transaction.atomic
def reject_timeoff(timeoff_id):
    """Reject time-off request"""
    timeoff = TimeOff.objects.get(id=timeoff_id)
    timeoff.status = TimeOff.Status.REJECTED
    timeoff.save()
    return timeoff


def get_pending_timeoffs(contract_id=None):
    """Get pending time-off requests"""
    queryset = TimeOff.objects.filter(status=TimeOff.Status.PENDING)
    if contract_id:
        queryset = queryset.filter(contract_id=contract_id)
    return queryset.order_by('-created_at')
