"""
Activity Logging Services
Tracks user activities for audit and security purposes
"""
from django.db import transaction
from django.utils import timezone
from .models_extended import ActivityLog


@transaction.atomic
def log_activity(user, action, resource_type=None, resource_id=None, 
                 ip_address=None, user_agent=None, metadata=None):
    """
    Log a user activity
    
    Args:
        user: User instance
        action: Action performed (e.g., 'LOGIN', 'CREATE_PROJECT', 'PAYMENT_RELEASED')
        resource_type: Type of resource (e.g., 'project', 'contract', 'payment')
        resource_id: ID of the resource
        ip_address: User's IP address
        user_agent: User's browser/client info
        metadata: Additional data as dict
    
    Returns:
        ActivityLog instance
    """
    return ActivityLog.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata or {}
    )


def get_user_activity_log(user, limit=50, action=None, resource_type=None):
    """
    Get activity log for a user
    
    Args:
        user: User instance
        limit: Number of records to return
        action: Filter by action type
        resource_type: Filter by resource type
    
    Returns:
        QuerySet of ActivityLog
    """
    queryset = ActivityLog.objects.filter(user=user)
    
    if action:
        queryset = queryset.filter(action=action)
    
    if resource_type:
        queryset = queryset.filter(resource_type=resource_type)
    
    return queryset.order_by('-created_at')[:limit]


def get_recent_logins(user, limit=10):
    """Get recent login activities for a user"""
    return ActivityLog.objects.filter(
        user=user,
        action='LOGIN'
    ).order_by('-created_at')[:limit]


def get_security_events(user, limit=20):
    """Get security-related events for a user"""
    security_actions = [
        'LOGIN',
        'LOGOUT',
        'PASSWORD_CHANGE',
        'PASSWORD_RESET',
        '2FA_ENABLED',
        '2FA_DISABLED',
        'FAILED_LOGIN'
    ]
    
    return ActivityLog.objects.filter(
        user=user,
        action__in=security_actions
    ).order_by('-created_at')[:limit]


def get_payment_activities(user, limit=20):
    """Get payment-related activities for a user"""
    payment_actions = [
        'PAYMENT_CREATED',
        'PAYMENT_RELEASED',
        'REFUND_PROCESSED',
        'DISPUTE_CREATED',
        'DISPUTE_RESOLVED'
    ]
    
    return ActivityLog.objects.filter(
        user=user,
        action__in=payment_actions
    ).order_by('-created_at')[:limit]


def get_activity_summary(user, days=30):
    """
    Get activity summary for a user
    
    Returns:
        Dict with activity counts by action type
    """
    from django.db.models import Count
    from datetime import timedelta
    
    since = timezone.now() - timedelta(days=days)
    
    summary = ActivityLog.objects.filter(
        user=user,
        created_at__gte=since
    ).values('action').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return {item['action']: item['count'] for item in summary}


# Activity action constants
class ActivityAction:
    # Authentication
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    REGISTER = 'REGISTER'
    PASSWORD_CHANGE = 'PASSWORD_CHANGE'
    PASSWORD_RESET = 'PASSWORD_RESET'
    FAILED_LOGIN = 'FAILED_LOGIN'
    
    # 2FA
    TWO_FA_ENABLED = '2FA_ENABLED'
    TWO_FA_DISABLED = '2FA_DISABLED'
    TWO_FA_VERIFIED = '2FA_VERIFIED'
    
    # Projects
    PROJECT_CREATED = 'PROJECT_CREATED'
    PROJECT_UPDATED = 'PROJECT_UPDATED'
    PROJECT_DELETED = 'PROJECT_DELETED'
    PROJECT_BOOKMARKED = 'PROJECT_BOOKMARKED'
    
    # Bidding
    BID_SUBMITTED = 'BID_SUBMITTED'
    BID_ACCEPTED = 'BID_ACCEPTED'
    BID_REJECTED = 'BID_REJECTED'
    BID_RETRACTED = 'BID_RETRACTED'
    
    # Contracts
    CONTRACT_CREATED = 'CONTRACT_CREATED'
    CONTRACT_COMPLETED = 'CONTRACT_COMPLETED'
    CONTRACT_TERMINATED = 'CONTRACT_TERMINATED'
    
    # Payments
    PAYMENT_CREATED = 'PAYMENT_CREATED'
    PAYMENT_RELEASED = 'PAYMENT_RELEASED'
    REFUND_PROCESSED = 'REFUND_PROCESSED'
    DISPUTE_CREATED = 'DISPUTE_CREATED'
    DISPUTE_RESOLVED = 'DISPUTE_RESOLVED'
    
    # Reviews
    REVIEW_SUBMITTED = 'REVIEW_SUBMITTED'
    REVIEW_RESPONDED = 'REVIEW_RESPONDED'
    
    # Profile
    PROFILE_UPDATED = 'PROFILE_UPDATED'
    AVATAR_UPDATED = 'AVATAR_UPDATED'
    ACCOUNT_DEACTIVATED = 'ACCOUNT_DEACTIVATED'
    ACCOUNT_REACTIVATED = 'ACCOUNT_REACTIVATED'
