from rest_framework import permissions
class IsConversationParticipant(permissions.BasePermission):
    """
    Permission that allows only the freelancer or client of a conversation.
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        return (
            obj.contract.bid.freelancer == user or
            obj.contract.bid.project.client == user
        )


class IsMessageSender(permissions.BasePermission):
    """
    Permission that allows only the sender of a message.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.sender == request.user


class CanSendMessage(permissions.BasePermission):
    """
    Permission that allows only participants of an active contract 
    to send messages.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        contract = obj.contract
        is_participant = (
            contract.bid.freelancer == user or
            contract.bid.project.client == user
        )
        is_active = contract.status == "ACTIVE"
        return is_participant and is_active
