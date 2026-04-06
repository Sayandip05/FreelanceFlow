from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from .models import Bid, Contract


def get_bid_by_id(bid_id: int) -> Bid:
    """Get bid by ID."""
    return get_object_or_404(Bid, id=bid_id)


def get_contract_by_id(contract_id: int) -> Contract:
    """Get contract by ID."""
    return get_object_or_404(Contract, id=contract_id)


def get_project_bids(project_id: int, status: str | None = None) -> QuerySet[Bid]:
    """
    Get all bids for a project.
    
    Args:
        project_id: Project ID
        status: Optional status filter
    
    Returns:
        QuerySet of Bid
    """
    queryset = Bid.objects.filter(
        project_id=project_id
    ).select_related('freelancer', 'project__client')
    
    if status:
        queryset = queryset.filter(status=status)
    
    return queryset


def get_freelancer_bids(freelancer, status: str | None = None) -> QuerySet[Bid]:
    """
    Get all bids by a freelancer.
    
    Args:
        freelancer: User instance
        status: Optional status filter
    
    Returns:
        QuerySet of Bid
    """
    queryset = Bid.objects.filter(
        freelancer=freelancer
    ).select_related('project', 'project__client')
    
    if status:
        queryset = queryset.filter(status=status)
    
    return queryset


def get_freelancer_active_contracts(freelancer) -> QuerySet[Contract]:
    """Get active contracts for a freelancer."""
    return Contract.objects.filter(
        bid__freelancer=freelancer,
        is_active=True
    ).select_related('bid__project', 'bid__freelancer')


def get_client_active_contracts(client) -> QuerySet[Contract]:
    """Get active contracts for a client."""
    return Contract.objects.filter(
        bid__project__client=client,
        is_active=True
    ).select_related('bid__project', 'bid__freelancer')


def has_freelancer_bid_on_project(freelancer, project_id: int) -> bool:
    """Check if freelancer has already bid on a project."""
    return Bid.objects.filter(
        freelancer=freelancer,
        project_id=project_id
    ).exists()


def get_contract_by_project(project_id: int) -> Contract | None:
    """Get contract for a project if exists."""
    try:
        return Contract.objects.get(bid__project_id=project_id)
    except Contract.DoesNotExist:
        return None
