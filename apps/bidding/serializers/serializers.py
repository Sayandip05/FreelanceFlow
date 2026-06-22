from rest_framework import serializers

from .models import Bid, Contract
from apps.users.serializers import UserSerializer
from apps.projects.serializers import ProjectListSerializer
from core.sanitizers import sanitize_html


class BidListSerializer(serializers.ModelSerializer):
    """Serializer for bid list view."""
    freelancer = UserSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    
    class Meta:
        model = Bid
        fields = [
            'id',
            'project',
            'freelancer',
            'amount',
            'status',
            'created_at',
            'updated_at',
        ]


class BidDetailSerializer(serializers.ModelSerializer):
    """Serializer for bid detail view."""
    freelancer = UserSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    
    class Meta:
        model = Bid
        fields = [
            'id',
            'project',
            'freelancer',
            'amount',
            'cover_letter',
            'status',
            'created_at',
            'updated_at',
        ]


class BidCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bids."""
    
    class Meta:
        model = Bid
        fields = ['project', 'amount', 'cover_letter']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Bid amount must be greater than 0.")
        return value
    
    def validate_cover_letter(self, value):
        if len(value.strip()) < 50:
            raise serializers.ValidationError(
                "Cover letter must be at least 50 characters."
            )
        # Sanitize cover letter to prevent XSS
        return sanitize_html(value, allow_basic_formatting=True)


class ContractSerializer(serializers.ModelSerializer):
    """Serializer for contracts."""
    project = ProjectListSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)
    client = UserSerializer(read_only=True)
    bid = BidDetailSerializer(read_only=True)
    
    class Meta:
        model = Contract
        fields = [
            'id',
            'bid',
            'project',
            'freelancer',
            'client',
            'agreed_amount',
            'start_date',
            'end_date',
            'is_active',
        ]


class ContractListSerializer(serializers.ModelSerializer):
    """Serializer for contract list view."""
    project_title = serializers.CharField(source='bid.project.title', read_only=True)
    freelancer_name = serializers.CharField(source='bid.freelancer.full_name', read_only=True)
    client_name = serializers.CharField(source='bid.project.client.full_name', read_only=True)
    
    class Meta:
        model = Contract
        fields = [
            'id',
            'project_title',
            'freelancer_name',
            'client_name',
            'agreed_amount',
            'start_date',
            'is_active',
        ]
