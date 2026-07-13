from rest_framework import permissions
from .models import Payment


class IsPaymentParticipant(permissions.BasePermission):
    """
    Permission that allows either the freelancer or client of a payment.
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        return (
            obj.contract.bid.freelancer == user or
            obj.contract.bid.project.client == user
        )


class IsPaymentClient(permissions.BasePermission):
    """
    Permission that allows only the client who made the payment.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.contract.bid.project.client == request.user


class IsPaymentFreelancer(permissions.BasePermission):
    """
    Permission that allows only the freelancer who receives the payment.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.contract.bid.freelancer == request.user
