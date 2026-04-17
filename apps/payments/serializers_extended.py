"""
Serializers for Extended Payment Features
"""
from rest_framework import serializers
from .models_extended import PaymentMilestone


class PaymentMilestoneSerializer(serializers.ModelSerializer):
    """Serializer for payment milestones"""
    contract_id = serializers.IntegerField(source='contract.id', read_only=True)
    project_title = serializers.CharField(
        source='contract.bid.project.title',
        read_only=True
    )
    freelancer_email = serializers.EmailField(
        source='contract.bid.freelancer.email',
        read_only=True
    )
    
    class Meta:
        model = PaymentMilestone
        fields = [
            'id', 'contract_id', 'project_title', 'freelancer_email',
            'title', 'description', 'amount', 'due_date',
            'status', 'created_at', 'completed_at', 'payment_id'
        ]
        read_only_fields = ['id', 'contract_id', 'project_title', 'freelancer_email', 'status', 'created_at', 'completed_at', 'payment_id']


class CreateMilestoneSerializer(serializers.Serializer):
    """Serializer for creating a milestone"""
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    due_date = serializers.DateField(required=False, allow_null=True)


class MilestoneProgressSerializer(serializers.Serializer):
    """Serializer for milestone progress"""
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    paid_count = serializers.IntegerField()
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
