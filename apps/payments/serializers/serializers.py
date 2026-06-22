from rest_framework import serializers

from .models import Payment, Escrow, PlatformEarning
from apps.bidding.serializers import ContractSerializer


class EscrowSerializer(serializers.ModelSerializer):
    """Serializer for escrow."""
    
    class Meta:
        model = Escrow
        fields = ['held_amount', 'released_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payments."""
    contract = ContractSerializer(read_only=True)
    escrow = EscrowSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'contract',
            'total_amount',
            'status',
            'razorpay_payout_id',
            'payout_error',
            'escrow',
            'created_at',
            'updated_at',
        ]


class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer for payment list view."""
    project_title = serializers.CharField(
        source='contract.bid.project.title',
        read_only=True
    )
    freelancer_name = serializers.CharField(
        source='contract.bid.freelancer.full_name',
        read_only=True
    )
    client_name = serializers.CharField(
        source='contract.bid.project.client.full_name',
        read_only=True
    )
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'project_title',
            'freelancer_name',
            'client_name',
            'total_amount',
            'status',
            'razorpay_payout_id',
            'created_at',
        ]


class CreateEscrowSerializer(serializers.Serializer):
    """Serializer for creating escrow."""
    contract_id = serializers.IntegerField()


class ReleasePaymentSerializer(serializers.Serializer):
    """Serializer for releasing payment."""
    contract_id = serializers.IntegerField()


class PlatformEarningSerializer(serializers.ModelSerializer):
    """Serializer for platform earnings."""
    
    class Meta:
        model = PlatformEarning
        fields = [
            'id',
            'cut_percentage',
            'cut_amount',
            'created_at',
        ]


class PaymentHistorySerializer(serializers.Serializer):
    """Serializer for payment history summary."""
    total_spent = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_earned = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_escrow = serializers.DecimalField(max_digits=15, decimal_places=2)
