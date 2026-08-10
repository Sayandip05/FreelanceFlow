from django.db.models import QuerySet, Sum
from django.shortcuts import get_object_or_404
from datetime import date, timedelta
from .models import WorkLog, WeeklyReport, DeliveryProof, Deliverable


def get_worklog_by_id(log_id: int) -> WorkLog:
    """Get work log by ID."""
    return get_object_or_404(WorkLog, id=log_id)


def get_contract_worklogs(
    contract_id: int,
    start_date: date | None = None,
    end_date: date | None = None
) -> QuerySet[WorkLog]:
    """
    Get work logs for a contract with optional date filtering.
    """
    queryset = WorkLog.objects.filter(
        contract_id=contract_id
    ).select_related(
        'freelancer',
        'freelancer__freelancer_profile',
        'freelancer__client_profile',
        'contract',
        'contract__bid__project',
        'contract__bid__project__client',
        'contract__bid__project__client__client_profile',
        'contract__bid__project__client__freelancer_profile',
        'contract__bid__freelancer',
        'contract__bid__freelancer__freelancer_profile',
        'contract__bid__freelancer__client_profile',
    ).prefetch_related(
        'contract__milestones',
        'contract__bid__project__skills'
    )
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    
    return queryset


def get_freelancer_worklogs(freelancer, contract_id: int | None = None) -> QuerySet[WorkLog]:
    """Get work logs for a freelancer."""
    queryset = WorkLog.objects.filter(freelancer=freelancer)
    
    if contract_id:
        queryset = queryset.filter(contract_id=contract_id)
    
    return queryset.select_related(
        'freelancer',
        'freelancer__freelancer_profile',
        'freelancer__client_profile',
        'contract',
        'contract__bid__project',
        'contract__bid__project__client',
        'contract__bid__project__client__client_profile',
        'contract__bid__project__client__freelancer_profile',
        'contract__bid__freelancer',
        'contract__bid__freelancer__freelancer_profile',
        'contract__bid__freelancer__client_profile',
    ).prefetch_related(
        'contract__milestones',
        'contract__bid__project__skills'
    )


def get_weekly_report_by_id(report_id: int) -> WeeklyReport:
    """Get weekly report by ID."""
    return get_object_or_404(
        WeeklyReport.objects.select_related(
            'contract',
            'contract__bid__project',
            'contract__bid__project__client',
            'contract__bid__project__client__client_profile',
            'contract__bid__project__client__freelancer_profile',
            'contract__bid__freelancer',
            'contract__bid__freelancer__freelancer_profile',
            'contract__bid__freelancer__client_profile',
        ).prefetch_related(
            'contract__milestones',
            'contract__bid__project__skills'
        ),
        id=report_id
    )


def get_contract_weekly_reports(contract_id: int) -> QuerySet[WeeklyReport]:
    """Get all weekly reports for a contract."""
    return WeeklyReport.objects.filter(
        contract_id=contract_id
    ).select_related(
        'contract',
        'contract__bid__project',
        'contract__bid__project__client',
        'contract__bid__project__client__client_profile',
        'contract__bid__project__client__freelancer_profile',
        'contract__bid__freelancer',
        'contract__bid__freelancer__freelancer_profile',
        'contract__bid__freelancer__client_profile',
    ).prefetch_related(
        'contract__milestones',
        'contract__bid__project__skills'
    )


def get_delivery_proof_by_contract(contract_id: int) -> DeliveryProof | None:
    """Get delivery proof for a contract."""
    try:
        return DeliveryProof.objects.select_related(
            'contract',
            'contract__bid__project',
            'contract__bid__project__client',
            'contract__bid__freelancer',
        ).get(contract_id=contract_id)
    except DeliveryProof.DoesNotExist:
        return None


def get_total_hours_for_contract(contract_id: int) -> float:
    """Get total hours logged for a contract."""
    result = WorkLog.objects.filter(
        contract_id=contract_id
    ).aggregate(total=Sum('hours_worked'))
    return result['total'] or 0


def get_week_logs(contract_id: int, week_start: date) -> QuerySet[WorkLog]:
    """Get logs for a specific week."""
    week_end = week_start + timedelta(days=6)
    return WorkLog.objects.filter(
        contract_id=contract_id,
        date__range=[week_start, week_end]
    ).select_related('freelancer').order_by('date')


def get_total_hours_for_week(contract_id: int, week_start: date) -> float:
    """Get total hours for a specific week."""
    week_end = week_start + timedelta(days=6)
    result = WorkLog.objects.filter(
        contract_id=contract_id,
        date__range=[week_start, week_end]
    ).aggregate(total=Sum('hours_worked'))
    return result['total'] or 0


def has_log_for_date(contract_id: int, log_date: date) -> bool:
    """Check if a log already exists for a date."""
    return WorkLog.objects.filter(
        contract_id=contract_id,
        date=log_date
    ).exists()


# ============================================================================
# DELIVERABLE SELECTORS
# ============================================================================

def get_deliverable_by_id(deliverable_id: int) -> Deliverable:
    """Get deliverable by ID."""
    return get_object_or_404(
        Deliverable.objects.select_related(
            'freelancer',
            'freelancer__freelancer_profile',
            'freelancer__client_profile',
            'reviewed_by',
            'reviewed_by__freelancer_profile',
            'reviewed_by__client_profile',
            'contract',
            'contract__bid__project',
            'contract__bid__project__client',
            'contract__bid__project__client__client_profile',
            'contract__bid__project__client__freelancer_profile',
            'contract__bid__freelancer',
            'contract__bid__freelancer__freelancer_profile',
            'contract__bid__freelancer__client_profile',
        ).prefetch_related(
            'contract__milestones',
            'contract__bid__project__skills'
        ),
        id=deliverable_id
    )


def get_contract_deliverables(
    contract_id: int,
    status: str | None = None
) -> QuerySet[Deliverable]:
    """
    Get deliverables for a contract with optional status filtering.
    """
    queryset = Deliverable.objects.filter(
        contract_id=contract_id
    ).select_related(
        'freelancer',
        'freelancer__freelancer_profile',
        'freelancer__client_profile',
        'reviewed_by',
        'reviewed_by__freelancer_profile',
        'reviewed_by__client_profile',
        'contract',
        'contract__bid__project',
        'contract__bid__project__client',
        'contract__bid__project__client__client_profile',
        'contract__bid__project__client__freelancer_profile',
        'contract__bid__freelancer',
        'contract__bid__freelancer__freelancer_profile',
        'contract__bid__freelancer__client_profile',
    ).prefetch_related(
        'contract__milestones',
        'contract__bid__project__skills'
    )
    
    if status:
        queryset = queryset.filter(status=status)
    
    return queryset


def get_freelancer_deliverables(
    freelancer,
    contract_id: int | None = None,
    status: str | None = None
) -> QuerySet[Deliverable]:
    """Get deliverables for a freelancer."""
    queryset = Deliverable.objects.filter(freelancer=freelancer)
    
    if contract_id:
        queryset = queryset.filter(contract_id=contract_id)
    if status:
        queryset = queryset.filter(status=status)
    
    return queryset.select_related(
        'freelancer',
        'freelancer__freelancer_profile',
        'freelancer__client_profile',
        'reviewed_by',
        'reviewed_by__freelancer_profile',
        'reviewed_by__client_profile',
        'contract',
        'contract__bid__project',
        'contract__bid__project__client',
        'contract__bid__project__client__client_profile',
        'contract__bid__project__client__freelancer_profile',
        'contract__bid__freelancer',
        'contract__bid__freelancer__freelancer_profile',
        'contract__bid__freelancer__client_profile',
    ).prefetch_related(
        'contract__milestones',
        'contract__bid__project__skills'
    )


def get_client_deliverables(
    client,
    contract_id: int | None = None,
    status: str | None = None
) -> QuerySet[Deliverable]:
    """Get deliverables for a client to review."""
    queryset = Deliverable.objects.filter(
        contract__bid__project__client=client
    )
    
    if contract_id:
        queryset = queryset.filter(contract_id=contract_id)
    if status:
        queryset = queryset.filter(status=status)
    
    return queryset.select_related(
        'freelancer',
        'freelancer__freelancer_profile',
        'freelancer__client_profile',
        'reviewed_by',
        'reviewed_by__freelancer_profile',
        'reviewed_by__client_profile',
        'contract',
        'contract__bid__project',
        'contract__bid__project__client',
        'contract__bid__project__client__client_profile',
        'contract__bid__project__client__freelancer_profile',
        'contract__bid__freelancer',
        'contract__bid__freelancer__freelancer_profile',
        'contract__bid__freelancer__client_profile',
    ).prefetch_related(
        'contract__milestones',
        'contract__bid__project__skills'
    )


def get_pending_approval_deliverables(client) -> QuerySet[Deliverable]:
    """Get deliverables pending client approval."""
    return Deliverable.objects.filter(
        contract__bid__project__client=client,
        status=Deliverable.Status.SUBMITTED
    ).select_related(
        'freelancer',
        'freelancer__freelancer_profile',
        'freelancer__client_profile',
        'reviewed_by',
        'reviewed_by__freelancer_profile',
        'reviewed_by__client_profile',
        'contract',
        'contract__bid__project',
        'contract__bid__project__client',
        'contract__bid__project__client__client_profile',
        'contract__bid__project__client__freelancer_profile',
        'contract__bid__freelancer',
        'contract__bid__freelancer__freelancer_profile',
        'contract__bid__freelancer__client_profile',
    ).prefetch_related(
        'contract__milestones',
        'contract__bid__project__skills'
    )


def get_approved_deliverables_for_contract(contract_id: int) -> QuerySet[Deliverable]:
    """Get all approved deliverables for a contract."""
    return Deliverable.objects.filter(
        contract_id=contract_id,
        status=Deliverable.Status.APPROVED
    )


def get_total_hours_from_deliverables(contract_id: int) -> float:
    """Get total hours from approved deliverables for a contract."""
    result = Deliverable.objects.filter(
        contract_id=contract_id,
        status=Deliverable.Status.APPROVED
    ).aggregate(total=Sum('hours_logged'))
    return result['total'] or 0
