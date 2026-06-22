"""
Serializers for Extended Bidding Features
"""
from rest_framework import serializers
from .models_extended import WorklogApproval, BidRetraction, CounterOffer


# ============= Worklog Approval Serializers =============

class WorklogApprovalSerializer(serializers.ModelSerializer):
    """Serializer for worklog approval"""
    worklog_id = serializers.IntegerField(source='worklog.id', read_only=True)
    worklog_date = serializers.DateField(source='worklog.date', read_only=True)
    worklog_hours = serializers.DecimalField(
        source='worklog.hours_worked',
        max_digits=4,
        decimal_places=2,
        read_only=True
    )
    freelancer_email = serializers.EmailField(
        source='worklog.freelancer.email',
        read_only=True
    )
    
    class Meta:
        model = WorklogApproval
        fields = [
            'id', 'worklog_id', 'worklog_date', 'worklog_hours',
            'freelancer_email', 'status', 'feedback',
            'approved_at', 'created_at'
        ]
        read_only_fields = fields


class ApproveWorklogSerializer(serializers.Serializer):
    """Serializer for approving worklog"""
    feedback = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional feedback for freelancer"
    )


class RejectWorklogSerializer(serializers.Serializer):
    """Serializer for rejecting worklog"""
    feedback = serializers.CharField(
        required=True,
        help_text="Feedback explaining rejection (required)"
    )


# ============= Bid Retraction Serializers =============

class BidRetractionSerializer(serializers.Serializer):
    """Serializer for retracting a bid"""
    reason = serializers.CharField(
        required=True,
        help_text="Reason for retracting the bid"
    )


class RetractionDetailSerializer(serializers.ModelSerializer):
    """Serializer for retraction details"""
    bid_id = serializers.IntegerField(source='bid.id', read_only=True)
    bid_amount = serializers.DecimalField(
        source='bid.amount',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    project_title = serializers.CharField(
        source='bid.project.title',
        read_only=True
    )
    
    class Meta:
        model = BidRetraction
        fields = ['id', 'bid_id', 'bid_amount', 'project_title', 'reason', 'retracted_at']
        read_only_fields = fields


# ============= Counter-Offer Serializers =============

class CounterOfferSerializer(serializers.Serializer):
    """Serializer for creating counter-offer"""
    counter_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        help_text="Counter-offered amount"
    )
    counter_timeline = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        help_text="Counter-offered timeline in days"
    )
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional message to freelancer"
    )


class CounterOfferResponseSerializer(serializers.ModelSerializer):
    """Serializer for counter-offer response"""
    bid_id = serializers.IntegerField(source='bid.id', read_only=True)
    original_amount = serializers.DecimalField(
        source='bid.amount',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    project_title = serializers.CharField(
        source='bid.project.title',
        read_only=True
    )
    offered_by_email = serializers.EmailField(
        source='offered_by.email',
        read_only=True
    )
    freelancer_email = serializers.EmailField(
        source='bid.freelancer.email',
        read_only=True
    )
    
    class Meta:
        model = CounterOffer
        fields = [
            'id', 'bid_id', 'original_amount', 'counter_amount',
            'counter_timeline', 'message', 'status',
            'project_title', 'offered_by_email', 'freelancer_email',
            'created_at', 'responded_at'
        ]
        read_only_fields = fields


class CounterOfferStatsSerializer(serializers.Serializer):
    """Serializer for counter-offer statistics"""
    sent = serializers.DictField()
    received = serializers.DictField()
