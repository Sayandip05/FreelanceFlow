from rest_framework import permissions

from .models import Bid, Contract


class IsBidOwner(permissions.BasePermission):
    """
    Permission that allows only the freelancer who submitted the bid.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.freelancer == request.user


class IsProjectClient(permissions.BasePermission):
    """
    Permission that allows only the client who posted the project.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.project.client == request.user


class IsContractParticipant(permissions.BasePermission):
    """
    Permission that allows either the freelancer or client of a contract.
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        return (
            obj.bid.freelancer == user or
            obj.bid.project.client == user
        )


class IsContractFreelancer(permissions.BasePermission):
    """
    Permission that allows only the contract's freelancer.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.bid.freelancer == request.user


class IsContractClient(permissions.BasePermission):
    """
    Permission that allows only the contract's client.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.bid.project.client == request.user
