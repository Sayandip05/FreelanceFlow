from rest_framework import permissions
from .models import WorkLog, WeeklyReport, DeliveryProof, Deliverable


class IsWorkLogFreelancer(permissions.BasePermission):
    """
    Permission that allows only the freelancer who created the log.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.freelancer == request.user


class IsContractParticipant(permissions.BasePermission):
    """
    Permission that allows either freelancer or client of the contract.
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if isinstance(obj, WorkLog):
            return (
                obj.freelancer == user or
                obj.contract.bid.project.client == user
            )
        elif isinstance(obj, WeeklyReport):
            return (
                obj.contract.bid.freelancer == user or
                obj.contract.bid.project.client == user
            )
        elif isinstance(obj, DeliveryProof):
            return (
                obj.contract.bid.freelancer == user or
                obj.contract.bid.project.client == user
            )
        return False


class IsContractFreelancer(permissions.BasePermission):
    """
    Permission that allows only the contract's freelancer.
    """
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, WorkLog):
            return obj.freelancer == request.user
        return obj.contract.bid.freelancer == request.user


class IsContractClient(permissions.BasePermission):
    """
    Permission that allows only the contract's client.
    """
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, WorkLog):
            return obj.contract.bid.project.client == request.user
        if isinstance(obj, Deliverable):
            return obj.contract.bid.project.client == request.user
        return obj.contract.bid.project.client == request.user
    
    def has_permission(self, request, view):
        # For list/create views, check contract param
        contract_id = request.query_params.get('contract')
        if contract_id and request.user.is_authenticated:
            from apps.bidding.models import Contract
            try:
                contract = Contract.objects.get(id=contract_id)
                return contract.bid.project.client == request.user
            except Contract.DoesNotExist:
                pass
        return request.user.is_authenticated
